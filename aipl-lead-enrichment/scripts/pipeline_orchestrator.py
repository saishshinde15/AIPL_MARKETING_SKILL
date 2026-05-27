"""
pipeline_orchestrator.py
========================
One-command end-to-end workflow for the AIPL lead enrichment skill.

The team uploads files and says "run AIPL pipeline" — this script figures out
what stage of the workflow they're in (Mode A starting, or Mode C merging tool
exports), runs the right step, and reports status.

State is tracked in the local cache (~/.aipl-cache/contacts.db) so the
orchestrator knows "Mode A ran 3 days ago, team is now uploading exports".

USAGE (from Claude analysis tool):
    from pipeline_orchestrator import run, detect_intent

    intent = detect_intent(['/mnt/user-data/uploads/foo.xlsx'])
    # → 'MODE_A_SOURCE' / 'MODE_C_TOOL_EXPORTS' / 'UNKNOWN'

    result = run(input_files=['/mnt/user-data/uploads/Limited_Medium_Enterprise.xlsx'],
                 output_dir='/mnt/user-data/outputs',
                 enrichment={})  # pass enrichment from web search, or {} to use cache only

    # For Mode C (merging exports):
    result = run(input_files=['lusha_export.csv', 'apollo_export.csv', 'master.xlsx'],
                 output_dir='/mnt/user-data/outputs')
"""
import os
import re
import sys
from pathlib import Path

import pandas as pd

# Skill scripts are in the same folder
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from build_vtiger_file  import build_files
from merge_tool_exports import merge_exports
from local_cache        import Cache

# Optional MCA / OpenCorporates lookup — graceful no-op if no API key set
try:
    from mca_lookup import lookup as mca_lookup, available as mca_available
except ImportError:
    mca_lookup = None
    def mca_available(): return False


# ---- Intent detection ----------------------------------------------------

SOURCE_COLUMNS  = {'enterprisename', 'enterprise name', 'company', 'company name'}
VTIGER_COLUMNS  = {'lead id', 'primary email', 'lead source'}  # uniquely Vtiger
TOOL_HINTS = {
    'Lusha':       {'linkedin url', 'work email', 'phone', 'mobile phone'},
    'Apollo':      {'organization name', 'corporate phone', 'email status'},
    'Signal Hire': {'email 1', 'phone 1', 'full name'},
    'Contact Out': {'personal email', 'work email'},
}


def _read_columns(path):
    """Best-effort header read for CSV or XLSX. Returns lowercase column set."""
    path = str(path)
    try:
        if path.lower().endswith('.csv'):
            df = pd.read_csv(path, nrows=0)
        else:
            df = pd.read_excel(path, nrows=0)
        return {str(c).strip().lower() for c in df.columns}
    except Exception:
        return set()


def detect_intent(file_paths):
    """
    Classify a set of uploaded files into one of:
      - MODE_A_SOURCE: at least one file looks like a raw company list
      - MODE_C_TOOL_EXPORTS: at least one file looks like a Lusha/Apollo/SH/CO export
      - MIXED: both kinds present (likely Mode C: master + exports)
      - UNKNOWN: can't tell

    Returns: (intent: str, details: dict with per-file classification)
    """
    classification = {}
    has_source = has_master = has_export = False

    for p in file_paths:
        cols = _read_columns(p)
        if not cols:
            classification[p] = 'unreadable'
            continue
        if cols & VTIGER_COLUMNS == VTIGER_COLUMNS:
            classification[p] = 'master_vtiger'
            has_master = True
        elif cols & SOURCE_COLUMNS:
            classification[p] = 'source_list'
            has_source = True
        else:
            # Tool export detection — which one?
            best_match, best_overlap = None, 0
            for tool, hints in TOOL_HINTS.items():
                overlap = len(cols & hints)
                if overlap >= 2 and overlap > best_overlap:
                    best_match, best_overlap = tool, overlap
            if best_match:
                classification[p] = f'tool_export:{best_match}'
                has_export = True
            elif 'company' in cols or 'company name' in cols:
                classification[p] = 'tool_export:Unknown'
                has_export = True
            else:
                classification[p] = 'unknown'

    if has_export and has_master:
        intent = 'MODE_C_TOOL_EXPORTS'
    elif has_export:
        intent = 'MODE_C_NEEDS_MASTER'   # need to find master separately
    elif has_source:
        intent = 'MODE_A_SOURCE'
    elif has_master and not has_export:
        intent = 'MODE_A_REBUILD'         # just rebuild from master (cache lookup)
    else:
        intent = 'UNKNOWN'

    return intent, classification


# ---- Pipeline runner -----------------------------------------------------

def run(input_files, output_dir, enrichment=None, filename_base='Hygienic_Leads'):
    """
    Detect intent + run the right mode.

    Returns dict:
        {
          'intent':      str,                # what we decided to do
          'classification': {path: type},    # per-file labels
          'outputs':     dict,               # file paths produced
          'summary':     str,                # plain-English summary for the user
          'next_action': str,                # what the user should do next
        }
    """
    intent, classification = detect_intent(input_files)
    outputs = {}
    summary_lines = []

    if intent in ('MODE_A_SOURCE', 'MODE_A_REBUILD'):
        # Find the source/master file
        src_path = next(p for p, kind in classification.items()
                        if kind in ('source_list', 'master_vtiger'))
        df = pd.read_excel(src_path) if src_path.lower().endswith('.xlsx') else pd.read_csv(src_path)
        df = df.fillna('')
        # Build companies list (use Vtiger row schema if master, else source schema)
        if classification[src_path] == 'master_vtiger':
            companies = [{'EnterpriseName': r.get('Company',''),
                          'Address': r.get('Street',''), 'State': r.get('State',''),
                          'District': r.get('City',''), 'Pincode': r.get('Postal Code','')}
                         for _, r in df.iterrows()]
        else:
            companies = df.to_dict('records')

        enrichment = dict(enrichment or {})

        # ---- v5.2: MCA / OpenCorporates auto-lookup for blanks (if key set) ----
        # Only runs when AIPL_OPENCORP_KEY env var is present. Free up to 50K/month.
        if mca_available() and mca_lookup:
            mca_filled = 0
            for c in companies:
                name = str(c.get('EnterpriseName','')).strip()
                if not name: continue
                existing = enrichment.get(name, {})
                # Only call MCA for companies we have ZERO info on
                if existing.get('first') or existing.get('last') or existing.get('email'):
                    continue
                try:
                    mca = mca_lookup(name)
                    if mca and mca.get('directors'):
                        d0 = mca['directors'][0]
                        full = d0.get('name','').strip().split(' ', 1)
                        existing.update({
                            'first':       existing.get('first') or (full[0] if full else ''),
                            'last':        existing.get('last')  or (full[1] if len(full)>1 else ''),
                            'designation': existing.get('designation') or d0.get('position',''),
                            'cin':         existing.get('cin') or mca.get('cin',''),
                            'source_url':  existing.get('source_url') or mca.get('source_url',''),
                            'confidence':  existing.get('confidence') or mca.get('confidence','Medium'),
                            'notes':       ((existing.get('notes','') + ' | ') if existing.get('notes') else '')
                                            + f"MCA via OpenCorporates: {mca.get('status','')}, "
                                              f"incorporated {mca.get('incorporation_date','?')}",
                        })
                        enrichment[name] = existing
                        mca_filled += 1
                except Exception:
                    pass
            if mca_filled:
                summary_lines.append(f"  (MCA auto-lookup filled {mca_filled} previously-blank cos)")

        outputs = build_files(companies, enrichment, output_dir, filename_base)

        # Stats
        out_df = pd.read_excel(outputs['xlsx']).fillna('')
        n = len(out_df)
        named = sum(1 for _, r in out_df.iterrows()
                    if str(r['First Name']).strip() or str(r['Last Name']).strip())
        emails = sum(1 for _, r in out_df.iterrows() if str(r['Primary Email']).strip())
        phones = sum(1 for _, r in out_df.iterrows()
                     if str(r['Office Phone']).strip() or str(r['Mobile Phone']).strip())

        summary_lines.append(f"Mode A complete — {n} companies processed.")
        summary_lines.append(f"  ✓ {named}/{n} contacts ({100*named//n if n else 0}%)")
        summary_lines.append(f"  ✓ {emails}/{n} with email")
        summary_lines.append(f"  ✓ {phones}/{n} with phone")
        next_action = (
            "Open Hygienic_Leads_Mode_B_Action_Sheet.md → work through it (~1 hour). "
            "When you're done with all 4 paid-tool exports, upload them back + say "
            "'merge these into the master file'."
        )

    elif intent in ('MODE_C_TOOL_EXPORTS', 'MODE_C_NEEDS_MASTER'):
        master = next((p for p, kind in classification.items() if kind == 'master_vtiger'), None)
        exports = [p for p, kind in classification.items() if kind.startswith('tool_export:')]
        if not master:
            return {
                'intent':         intent,
                'classification': classification,
                'outputs':        {},
                'summary':        'Found tool exports but no master Vtiger file.',
                'next_action':    "Please also upload the Hygienic_Leads.xlsx from your last Mode A run.",
            }
        outputs = merge_exports(master_file=master, export_files=exports,
                                output_dir=output_dir, filename_base=filename_base + '_Updated')
        summary_lines.append(f"Mode C complete — merged {len(exports)} tool export(s) "
                             f"into master.")
        summary_lines.append(f"  ✓ {outputs.get('updated',0)} master rows updated")
        summary_lines.append(f"  ⊘ {outputs.get('skipped',0)} export rows skipped (no master match)")
        for td in outputs.get('tools_detected', []):
            summary_lines.append(f"  • {td['file']} → {td['tool']} ({td['rows']} rows)")
        next_action = "Download Hygienic_Leads_Updated.csv and import into Vtiger."

    else:
        return {
            'intent':         intent,
            'classification': classification,
            'outputs':        {},
            'summary':        "Couldn't tell what to do with the uploaded files.",
            'next_action':    ("If this is a company list to enrich: rename a column to 'EnterpriseName' "
                              "or 'Company'. If this is tool exports for merging: upload them with the "
                              "master Hygienic_Leads.xlsx in the same chat."),
        }

    return {
        'intent':         intent,
        'classification': classification,
        'outputs':        outputs,
        'summary':        '\n'.join(summary_lines),
        'next_action':    next_action,
    }


def cache_status():
    """Return current cache state for status messages."""
    c = Cache()
    s = c.stats()
    c.close()
    return s


if __name__ == "__main__":
    # Quick smoke test
    print("=== Pipeline orchestrator ===")
    print(f"Cache state: {cache_status()}")
    src = '/Users/saish/Downloads/AIPL MAIN/Marketing /Limited Medium Enterprise.xlsx'
    if os.path.exists(src):
        intent, cls = detect_intent([src])
        print(f"\nIntent for source file: {intent}")
        print(f"Classification: {cls}")
