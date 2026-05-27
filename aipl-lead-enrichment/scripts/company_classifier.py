"""
company_classifier.py
=====================
Classifies each Indian company by legal type. Different types need different
research strategies (Cooperative societies aren't on MCA, Nidhis are regulated
by RBI, LLPs need LLPIN not CIN, etc.).

The classifier reads the company name (and optionally the CIN if available) and
returns a structured type record the rest of the skill can route on.

USAGE:
    from company_classifier import classify
    info = classify("M/S MAGBLISS INFOTECH PRIVATE LIMITED")
    # → {'type': 'Pvt Ltd', 'registrar': 'MCA', 'research_strategy': 'standard',
    #    'sales_fit': 'medium', 'notes': '...'}
"""
import re

TYPES = {
    # ---- Order matters: most specific patterns FIRST ----
    'LLP': {
        'patterns': [r'\blimited\s+liability\s+partnership\b', r'\bllp\b'],
        'registrar': 'MCA (LLPIN)',
        'research_strategy': 'llp',  # Designated Partners not Directors
        'sales_fit': 'medium',  # usually small/mid
        'expected_data': 'Designated Partners on MCA. Small team, no IT-specific role usually.',
    },
    'Cooperative Society': {
        'patterns': [r'\bsahakari\b', r'\bpatsantha\b',
                     r'\bco[\s-]?operative\b', r'\bcooperative\s+society\b'],
        'registrar': 'State Co-op Registrar',
        'research_strategy': 'skip',  # not on MCA, very limited web presence
        'sales_fit': 'low',  # low IT budgets typically
        'expected_data': 'Not in MCA. State registrar holds records (often offline).',
    },
    'Nidhi / NBFC-Nidhi': {
        'patterns': [r'\bnidhi\b'],
        'registrar': 'MCA + RBI',
        'research_strategy': 'minimal',  # niche financial, tiny ops
        'sales_fit': 'low',
        'expected_data': 'Small NBFC. Directors on MCA. Rarely needs enterprise IT.',
    },
    'Producer Company': {
        'patterns': [r'\bproducer\s+company\b', r'\bshetkari\b.*\b(mahila\s+)?producer\b'],
        'registrar': 'MCA (Producer Co.)',
        'research_strategy': 'minimal',
        'sales_fit': 'very_low',  # rural agriculture cos, minimal IT spend
        'expected_data': 'Farmer-led co. Directors are usually farmers; no IT role.',
    },
    'OPC (One Person Company)': {
        'patterns': [r'\bopc\b', r'\bone\s+person\s+company\b'],
        'registrar': 'MCA',
        'research_strategy': 'standard',
        'sales_fit': 'low',  # single-person companies = no IT team
        'expected_data': 'Single Director. Owner is the IT decision-maker by default.',
    },
    'Section 8 (NGO)': {
        'patterns': [r'\bsection\s+8\b', r'\bnot\s+for\s+profit\b'],
        'registrar': 'MCA',
        'research_strategy': 'minimal',
        'sales_fit': 'very_low',
        'expected_data': 'Non-profit. Usually no IT budget.',
    },
    'Partnership Firm': {
        'patterns': [r'\bpartnership\s+firm\b'],
        'registrar': 'Registrar of Firms (state)',
        'research_strategy': 'skip',
        'sales_fit': 'medium',
        'expected_data': 'Not on MCA. Hard to research via public sources.',
    },
    # ---- Generic / catch-all types LAST ----
    'Pvt Ltd': {
        'patterns': [r'\bprivate\s+limited\b', r'\bpvt\.?\s*ltd\.?\b',
                     r'\bpvt\.?\s*limited\b'],
        'registrar': 'MCA',
        'research_strategy': 'standard',
        'sales_fit': 'high',
        'expected_data': 'Director name + CIN + address; rarely IT-specific contact',
    },
    'Public Ltd': {
        'patterns': [r'\blimited\b', r'\bltd\.?\b'],
        'registrar': 'MCA',
        'research_strategy': 'enhanced',
        'sales_fit': 'very_high',
        'expected_data': 'Often has dedicated IT Head on LinkedIn + investor pages',
    },
}

# Used to detect if a CIN prefix gives us extra info
CIN_PREFIXES = {
    'L': 'Listed Public',
    'U': 'Unlisted',
}
CIN_SUFFIX_CLASS = {
    'PTC': 'Private',
    'PLC': 'Public',
    'NPL': 'Section 8',
    'OPC': 'OPC',
    'FTC': 'Foreign Private',
    'GOI': 'Government',
}


def classify(company_name, cin=''):
    """
    Returns:
        {
          'type':              str,
          'registrar':         str,
          'research_strategy': str,  # 'standard'/'enhanced'/'llp'/'skip'/'minimal'
          'sales_fit':         str,  # 'very_high'/'high'/'medium'/'low'/'very_low'
          'expected_data':     str,
          'notes':             str,
        }
    """
    if not company_name:
        return {'type': 'Unknown', 'registrar': '', 'research_strategy': 'standard',
                'sales_fit': 'medium', 'expected_data': '', 'notes': 'No company name'}

    name = str(company_name).upper()
    notes = []

    # Try each type's regex
    for type_name, spec in TYPES.items():
        for pat in spec['patterns']:
            if re.search(pat, name, re.IGNORECASE):
                result = {
                    'type':              type_name,
                    'registrar':         spec['registrar'],
                    'research_strategy': spec['research_strategy'],
                    'sales_fit':         spec['sales_fit'],
                    'expected_data':     spec['expected_data'],
                    'notes':             '',
                }
                # Augment with CIN-derived info if present
                if cin:
                    cin_up = cin.upper().strip()
                    if cin_up.startswith('L'):
                        notes.append('CIN starts with L → BSE/NSE-listed')
                        if result['type'] == 'Pvt Ltd':
                            result['type'] = 'Public Ltd'
                            result['research_strategy'] = 'enhanced'
                            result['sales_fit'] = 'very_high'
                    elif cin_up.startswith('U'):
                        notes.append('CIN starts with U → unlisted')
                    m = re.search(r'([A-Z]{3})', cin_up[5:9] if len(cin_up) >= 9 else cin_up)
                    if m:
                        suffix_meaning = CIN_SUFFIX_CLASS.get(m.group(1))
                        if suffix_meaning:
                            notes.append(f'CIN suffix {m.group(1)} → {suffix_meaning}')
                result['notes'] = '; '.join(notes)
                return result

    # No pattern matched — default to "Limited" with bare assumptions
    return {
        'type':              'Unknown',
        'registrar':         'Unknown',
        'research_strategy': 'standard',
        'sales_fit':         'medium',
        'expected_data':     'Unable to classify legal type from name',
        'notes':             'Generic name — could be Pvt Ltd, partnership, or proprietorship',
    }


if __name__ == '__main__':
    tests = [
        ("M/S MAGBLISS INFOTECH PRIVATE LIMITED", ''),
        ("BATLIBOI LIMITED", ''),
        ("M/S STAR SYNDICATE LIMITED LIABILITY PARTNERSHIP", ''),
        ("DEEPSTAMBH BEROJGAR SEVA SAHAKARI SANSTHA LTD", ''),
        ("M/S TRILOKNATH NIDHI LIMITED", ''),
        ("M/S PURANDAR LAXMI SHETKARI MAHILA PRODUCER COMPANY LIMITED", ''),
        ("Motilal Oswal Financial Services Ltd", 'L67190MH2005PLC153397'),
    ]
    for name, cin in tests:
        info = classify(name, cin)
        print(f"{name[:55]:<55}")
        print(f"  type={info['type']:<25} strategy={info['research_strategy']:<10} fit={info['sales_fit']}")
        if info['notes']:
            print(f"  notes: {info['notes']}")
        print()
