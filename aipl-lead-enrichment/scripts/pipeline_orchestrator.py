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

# v6: schema normalization — handles weird column names in input files
try:
    from schema_detector import normalize_dataframe
    _HAS_SCHEMA_DETECTOR = True
except ImportError:
    _HAS_SCHEMA_DETECTOR = False

# v6: data sanitization — fixes typos, pincodes, addresses, state names
try:
    from data_sanitizer import sanitize_dataframe
    _HAS_DATA_SANITIZER = True
except ImportError:
    _HAS_DATA_SANITIZER = False

# v6: company classifier — Pvt Ltd / LLP / Cooperative / Nidhi / etc.
try:
    from company_classifier import classify as classify_company
    _HAS_COMPANY_CLASSIFIER = True
except ImportError:
    _HAS_COMPANY_CLASSIFIER = False


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


def _has_company_content(path):
    """
    v7.3: detect whether a header-less file actually contains company names.
    Used to classify files with Unnamed columns as source lists.
    """
    if not _HAS_SCHEMA_DETECTOR:
        return False
    try:
        from schema_detector import detect_headerless
        if str(path).lower().endswith('.xlsx'):
            df = pd.read_excel(path, nrows=50)
        else:
            df = pd.read_csv(path, nrows=50)
        rename_map, _ = detect_headerless(df)
        return 'EnterpriseName' in rename_map.values()
    except Exception:
        return False


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
            # v7.3: header read failed (e.g. odd xlsx) — try content detection
            if _has_company_content(p):
                classification[p] = 'source_list'
                has_source = True
            else:
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
            elif _has_company_content(p):
                # v7.3: header-less file (Unnamed cols) but content looks like
                # a company list — treat as source list
                classification[p] = 'source_list'
                has_source = True
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


# ---- Deep search planning -------------------------------------------------

# Company types that deep search CANNOT recover (no digital footprint)
_UNREACHABLE_TYPES = ('Cooperative Society', 'Nidhi / NBFC-Nidhi',
                      'Producer Company', 'Section 8 (NGO)', 'Partnership Firm')


def deep_search_plan(output_xlsx_path):
    """
    Analyze a generated XLSX, identify blank companies worth deep-searching,
    and return a plan + warning message the team must see before triggering it.

    Returns dict:
        {
          'blanks_total':       int,
          'worth_searching':    [company names],   # exclude unreachable types
          'unreachable':        [company names],   # cooperatives/Nidhi/etc.
          'est_messages':       int,                # Claude message cost estimate
          'est_recovery':       str,                # realistic coverage gain
          'warning':            str,                # the message to show the team
        }
    """
    df = pd.read_excel(output_xlsx_path).fillna('')

    try:
        from company_classifier import classify as _classify
    except ImportError:
        _classify = None

    def _is_blank(r):
        return not (str(r.get('First Name','')).strip() or str(r.get('Last Name','')).strip())

    worth, unreachable = [], []
    for _, r in df.iterrows():
        if not _is_blank(r):
            continue
        name = str(r.get('Company',''))
        ctype = _classify(name)['type'] if _classify else 'Unknown'
        if ctype in _UNREACHABLE_TYPES:
            unreachable.append(name)
        else:
            worth.append(name)

    n_worth = len(worth)
    est_msgs = max(3, round(n_worth * 1.3))   # ~1.3 Claude messages per deep-searched co
    # Realistic recovery: ~40-50% of the worth-searching blanks
    est_recovered = round(n_worth * 0.45)

    warning = (
        f"⚠️  DEEP SEARCH — please read before confirming\n"
        f"\n"
        f"What it does: aggressively researches the {n_worth} blank companies that\n"
        f"MIGHT be findable — using LinkedIn company pages, press releases, annual\n"
        f"reports, news, and multiple search angles per company.\n"
        f"\n"
        f"⏱  COST: about {est_msgs} Claude messages in one go. On the $20 Pro plan\n"
        f"   that is a big chunk of your 5-hour message limit. You may not be able to\n"
        f"   run much else in Claude for the next few hours after this.\n"
        f"\n"
        f"🎯 REALISTIC RESULT: recovers roughly {est_recovered} of the {n_worth} blanks\n"
        f"   (~45%). The rest genuinely have no findable online presence.\n"
        f"\n"
        f"🚫 SKIPPED ({len(unreachable)} companies): cooperatives, Nidhis, producer\n"
        f"   companies — these aren't on any online registry, deep search can't help.\n"
        f"\n"
        f"💡 TIP: You don't have to do this every week. Run the normal (fast) enrichment\n"
        f"   weekly, and only run Deep Search once a month on accumulated blanks — the\n"
        f"   results get cached so you never re-pay this cost for the same company.\n"
        f"\n"
        f"Reply 'yes deep search' to proceed, or 'skip' to keep the current results."
    )

    return {
        'blanks_total':    n_worth + len(unreachable),
        'worth_searching': worth,
        'unreachable':     unreachable,
        'est_messages':    est_msgs,
        'est_recovery':    f"~{est_recovered} of {n_worth} blanks (~45%)",
        'warning':         warning,
    }


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

        # v7.3: read ALL sheets in an xlsx and combine (AIPL files sometimes
        # split data across sheets like "Group - RP DB" + "Private - RP DB")
        if src_path.lower().endswith('.xlsx'):
            xl = pd.ExcelFile(src_path)
            if len(xl.sheet_names) > 1:
                frames = []
                for sh in xl.sheet_names:
                    sdf = xl.parse(sh)
                    if len(sdf) > 0:
                        sdf['_source_sheet'] = sh
                        frames.append(sdf)
                df = pd.concat(frames, ignore_index=True) if frames else xl.parse(xl.sheet_names[0])
                summary_lines.append(f"(Combined {len(xl.sheet_names)} sheets: {', '.join(xl.sheet_names)})")
            else:
                df = xl.parse(xl.sheet_names[0])
        else:
            df = pd.read_csv(src_path)
        df = df.fillna('')

        # v7.3: large-file guard — warn about Claude-message cost before processing
        if len(df) > 200:
            est_min = max(5, len(df) // 20)
            summary_lines.append(
                f"⚠ LARGE FILE: {len(df)} companies. Full fresh research would take "
                f"~{est_min}-{est_min*2} min and a big chunk of your Claude message "
                f"budget. Cached companies are instant; only blanks cost messages. "
                f"If this is a one-time bulk load, consider splitting into ~200-row "
                f"batches across a few sessions.")

        # v6: auto-normalize variable column names (Company/EnterpriseName/etc.)
        if _HAS_SCHEMA_DETECTOR and classification[src_path] == 'source_list':
            df, mapping, sch_warnings = normalize_dataframe(df)
            if mapping:
                rename_msg = '; '.join(f"'{k}'→{v}" for k,v in mapping.items() if k != v)
                if rename_msg:
                    summary_lines.append(f"(Auto-renamed input columns: {rename_msg})")
            for w in sch_warnings:
                if w.startswith('❌'):
                    return {'intent': intent, 'classification': classification, 'outputs': {},
                            'summary': w, 'next_action': 'Add the missing column to your file and re-upload.'}

        # v6: sanitize cells (typos like "PR IVA TE", pincode .0 suffix, state abbreviations)
        if _HAS_DATA_SANITIZER:
            df, changes = sanitize_dataframe(df)
            if changes:
                summary_lines.append(f"(Sanitized {changes} cells: pincodes, addresses, typos)")

        # ---- v7.1: Dedupe by normalized company name ----
        import re as _re
        def _normkey(s):
            s = _re.sub(r'\bm/s\s+', '', str(s or '').upper())
            for sfx in ['PRIVATE LIMITED','PVT LTD','PVT. LTD','PVT LIMITED',
                        'LIMITED',' LTD',' LLP','LIABILITY PARTNERSHIP']:
                s = s.replace(sfx, ' ')
            return _re.sub(r'\s+', ' ', s).strip()
        if 'EnterpriseName' in df.columns:
            df['_dedup_key'] = df['EnterpriseName'].apply(_normkey)
            before = len(df)
            df = df.drop_duplicates(subset=['_dedup_key'], keep='first').drop(columns=['_dedup_key']).reset_index(drop=True)
            if len(df) < before:
                summary_lines.append(f"(Deduped {before - len(df)} duplicate company rows)")

        # ---- v7.1: Harvest pre-populated enrichment columns into enrichment dict ----
        # If input ALREADY has Phone/Email/Name columns filled, use that as trusted
        # starting data — skill only researches genuine blanks.
        enrichment = dict(enrichment or {})
        existing_cols = set(df.columns)
        enrichable_fields = {
            'First Name':    'first',
            'Last Name':     'last',
            'Designation':   'designation',
            'Primary Email': 'email',
            'Office Phone':  'phone',
            'Mobile Phone':  'mobile',
            'Website':       'website',
            'Industry':      'industry',
        }
        harvested = 0
        for _, row in df.iterrows():
            name = str(row.get('EnterpriseName','')).strip()
            if not name:
                continue
            existing_enr = enrichment.get(name, {})
            row_data = {}
            for col, key in enrichable_fields.items():
                if col in existing_cols:
                    val = str(row[col]).strip()
                    if val and val.lower() != 'nan' and not existing_enr.get(key):
                        row_data[key] = val
            if row_data:
                row_data.setdefault('source_url', 'Provided in input file')
                row_data.setdefault('confidence', 'High')  # input data trusted
                row_data.setdefault('notes', 'From input file (preserved as-is)')
                enrichment[name] = {**existing_enr, **row_data}
                harvested += 1
        if harvested:
            summary_lines.append(f"(Used pre-populated data from {harvested} input rows — skill researched only the blanks)")
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
