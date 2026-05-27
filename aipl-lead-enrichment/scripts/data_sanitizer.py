"""
data_sanitizer.py
=================
Cleans malformed data in input rows before downstream enrichment.

Handles:
- Pincode variants (string "400001", float 400001.0, "400 001", "PIN: 400001")
- Address whitespace, line breaks, repeated punctuation
- Company-name typos (extra spaces inside words: "PR IVA TE", normalizing "M/S " prefix)
- State name variants (MH, Maharashtra, MAHARASTRA, etc.)
- City/district variants

Pure Python. Zero LLM calls. Called by pipeline_orchestrator BEFORE enrichment.
"""
import re

# State abbreviation → canonical
STATE_CANONICAL = {
    'MH': 'Maharashtra', 'MAHARASHTRA': 'Maharashtra', 'MAHARASTRA': 'Maharashtra',
    'KA': 'Karnataka', 'KARNATAKA': 'Karnataka',
    'TN': 'Tamil Nadu', 'TAMIL NADU': 'Tamil Nadu', 'TAMILNADU': 'Tamil Nadu',
    'KL': 'Kerala', 'KERALA': 'Kerala',
    'AP': 'Andhra Pradesh', 'ANDHRA PRADESH': 'Andhra Pradesh',
    'TS': 'Telangana', 'TELANGANA': 'Telangana',
    'GJ': 'Gujarat', 'GUJARAT': 'Gujarat',
    'DL': 'Delhi', 'DELHI': 'Delhi', 'NEW DELHI': 'Delhi',
    'UP': 'Uttar Pradesh', 'UTTAR PRADESH': 'Uttar Pradesh',
    'WB': 'West Bengal', 'WEST BENGAL': 'West Bengal',
    'HR': 'Haryana', 'HARYANA': 'Haryana',
    'RJ': 'Rajasthan', 'RAJASTHAN': 'Rajasthan',
    'PB': 'Punjab', 'PUNJAB': 'Punjab',
    'GA': 'Goa', 'GOA': 'Goa',
    'MP': 'Madhya Pradesh', 'MADHYA PRADESH': 'Madhya Pradesh',
}

# Common Mumbai/Pune/Thane area variants → canonical city
CITY_CANONICAL = {
    'NAVI MUMBAI': 'Navi Mumbai', 'MUMBAI CITY': 'Mumbai', 'MUMBAI': 'Mumbai',
    'KALYAN': 'Kalyan', 'KALYAN EAST': 'Kalyan', 'KALYAN WEST': 'Kalyan',
    'PUNE': 'Pune', 'PUNE CITY': 'Pune',
    'THANE': 'Thane', 'THANE WEST': 'Thane', 'THANE EAST': 'Thane',
    'BYCULLA': 'Byculla', 'TITWALA': 'Titwala', 'WORLI': 'Mumbai',
    'PAWANE': 'Navi Mumbai', 'BELAPUR': 'Navi Mumbai', 'VASHI': 'Navi Mumbai',
    'NERUL': 'Navi Mumbai', 'VIKHROLI': 'Mumbai', 'POWAI': 'Mumbai',
    'ANDHERI': 'Mumbai', 'BORIVALI': 'Mumbai', 'GOREGAON': 'Mumbai',
    'CHEMBUR': 'Mumbai', 'KURLA': 'Mumbai', 'BANDRA': 'Mumbai',
}


def clean_pincode(v):
    """Return a 6-digit Indian pincode string or '' if not valid."""
    if v is None: return ''
    s = str(v).strip()
    if not s or s.lower() == 'nan':
        return ''
    # Strip "PIN:" / "Pincode:" prefixes
    s = re.sub(r'(?i)^(pin\s*code\s*:?|pin\s*:?|postal\s*code\s*:?)\s*', '', s)
    # Float values from Excel: "400001.0" → "400001"
    s = re.sub(r'\.0+$', '', s)
    digits = re.sub(r'\D', '', s)
    return digits if len(digits) == 6 else ''


def clean_state(v):
    """Normalize Indian state names + abbreviations."""
    if v is None: return ''
    s = str(v).strip().upper()
    if not s or s == 'NAN': return ''
    return STATE_CANONICAL.get(s, s.title())


def clean_city(v):
    """Normalize Mumbai/Pune/Thane area variants."""
    if v is None: return ''
    s = str(v).strip().upper()
    if not s or s == 'NAN': return ''
    return CITY_CANONICAL.get(s, s.title())


def clean_company_name(v):
    """
    Fix common typos in Indian company-name source data:
    - "PR IVA TE LIMITED" → "PRIVATE LIMITED"
    - "PRIVATELIMITED" → "PRIVATE LIMITED" (when stuck together)
    - Multi-space collapse
    - Leading/trailing punctuation strip
    Preserves "M/S " prefix (handled elsewhere for matching).
    """
    if v is None: return ''
    s = str(v).strip()
    if not s or s.lower() == 'nan': return ''

    # Common typo patterns
    fixes = [
        (r'\bPR\s+IVA\s+TE\b', 'PRIVATE'),       # PR IVA TE
        (r'\bP\s*V\s*T\s+LTD\b', 'PVT LTD'),     # P V T LTD
        (r'PRIVATELIMITED\b', 'PRIVATE LIMITED'),
        (r'PVTLTD\b', 'PVT LTD'),
        (r'\bP\s+L\s+T\s+D\b', 'PVT LTD'),
    ]
    for pat, rep in fixes:
        s = re.sub(pat, rep, s, flags=re.IGNORECASE)

    # Collapse whitespace, strip stray punctuation at ends
    s = re.sub(r'\s+', ' ', s).strip(' ,.;:')
    return s


def clean_address(v):
    """Clean addresses: collapse newlines/multi-spaces, remove repeat punctuation."""
    if v is None: return ''
    s = str(v).strip()
    if not s or s.lower() == 'nan': return ''
    # Convert newlines/tabs → comma+space
    s = re.sub(r'[\n\t\r]+', ', ', s)
    # Collapse multi-commas
    s = re.sub(r',\s*,+', ',', s)
    # Collapse multi-spaces
    s = re.sub(r'\s+', ' ', s)
    return s.strip(' ,.;:')


def sanitize_row(row):
    """
    Apply all field-level cleaners to one row dict (mutates in place + returns).
    Operates on canonical schema field names.
    """
    if 'EnterpriseName' in row:
        row['EnterpriseName'] = clean_company_name(row['EnterpriseName'])
    if 'Company' in row:
        row['Company'] = clean_company_name(row['Company'])
    if 'Address' in row:
        row['Address'] = clean_address(row['Address'])
    if 'State' in row:
        row['State'] = clean_state(row['State'])
    if 'District' in row:
        row['District'] = clean_city(row['District'])
    if 'City' in row:
        row['City'] = clean_city(row['City'])
    if 'Pincode' in row:
        row['Pincode'] = clean_pincode(row['Pincode'])
    return row


def sanitize_dataframe(df):
    """Apply sanitization to every row of a DataFrame. Returns count of changes."""
    changes = 0
    for col, cleaner in [
        ('EnterpriseName', clean_company_name),
        ('Company',        clean_company_name),
        ('Address',        clean_address),
        ('State',          clean_state),
        ('District',       clean_city),
        ('City',           clean_city),
        ('Pincode',        clean_pincode),
    ]:
        if col in df.columns:
            before = df[col].astype(str).tolist()
            df[col] = df[col].apply(cleaner)
            after = df[col].astype(str).tolist()
            changes += sum(1 for b, a in zip(before, after) if b != a)
    return df, changes


if __name__ == '__main__':
    # Self-test
    tests = [
        {'EnterpriseName': 'M/S HETUL CONSTRUCTION PR IVA TE LIMITED',
         'Address':  'Office no 5,\nMG Road,\nThane',
         'State':    'MH',  'District': 'THANE WEST',  'Pincode': '421306.0'},
        {'EnterpriseName': 'PREMIERGLASSPRIVATELIMITED',
         'Pincode':  'PIN: 400 021',  'State': 'MAHARASTRA'},
        {'EnterpriseName': '  Motilal  Oswal   Financial    Services  Ltd  ',
         'Address':  ',,, , Mumbai, ,,', 'City': 'mumbai'},
    ]
    for t in tests:
        cleaned = sanitize_row(dict(t))
        print(f'BEFORE: {t}')
        print(f'AFTER:  {cleaned}\n')
