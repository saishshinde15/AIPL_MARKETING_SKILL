"""
schema_detector.py
==================
Auto-detects + normalizes inconsistent input file schemas.

AIPL's weekly source files vary in column names. This module maps any reasonable
variant onto the canonical schema the rest of the skill expects.

Canonical schema:
    EnterpriseName, Address, State, District, Pincode

USAGE:
    from schema_detector import normalize_dataframe
    src_df, mapping, warnings = normalize_dataframe(src_df)
    # df now has canonical column names; mapping shows what was renamed;
    # warnings lists missing required cols
"""
import re

# Canonical → list of acceptable input variants (case-insensitive, whitespace-tolerant)
CANONICAL_VARIANTS = {
    # ---- Core company-identity columns (always required) ----
    'EnterpriseName': [
        'enterprisename', 'enterprise name', 'enterprise',
        'company', 'company name', 'companyname',
        'organisation', 'organization', 'organisation name', 'organization name',
        'name', 'name of company', 'name of business', 'name of organization',
        'firm', 'firm name', 'business', 'business name', 'entity', 'entity name',
        'company/firm', 'co name', 'co. name', 'account', 'account name',
    ],
    'Address': [
        'address', 'office address', 'registered address', 'registered office',
        'registered office address', 'address of business', 'business address',
        'street', 'street address', 'location', 'full address', 'reg office',
        'reg. office', 'reg address', 'office', 'building address',
        'corporate address', 'principal place of business',
    ],
    'State': [
        'state', 'state name', 'province', 'region', 'st',
    ],
    'District': [
        'district', 'district name', 'city', 'city name', 'town', 'taluka',
        'place', 'city/district', 'location city', 'office city',
    ],
    'Pincode': [
        'pincode', 'pin code', 'pin', 'postal code', 'zip', 'zip code',
        'postal', 'postcode', 'zipcode', 'pin no', 'pin number',
    ],
    # ---- v7.1: Pre-populated enrichment columns (use as starting point if present) ----
    'First Name': [
        'first name', 'firstname', 'fname', 'given name', 'contact first name',
        'first', 'contact name',
    ],
    'Last Name': [
        'last name', 'lastname', 'lname', 'surname', 'family name',
        'contact last name', 'last',
    ],
    'Designation': [
        'designation', 'title', 'job title', 'role', 'position',
        'job role', 'contact title',
    ],
    'Primary Email': [
        'email', 'email address', 'primary email', 'work email', 'business email',
        'mail', 'e-mail', 'contact email', 'email id', 'official email',
    ],
    'Office Phone': [
        'phone', 'office phone', 'work phone', 'business phone', 'landline',
        'tel', 'telephone', 'switchboard', 'contact number', 'phone number',
        'office number',
    ],
    'Mobile Phone': [
        'mobile', 'mobile phone', 'mobile number', 'cell', 'cell phone',
        'cellphone', 'direct dial', 'direct phone', 'whatsapp', 'mob',
    ],
    'Website': [
        'website', 'web', 'url', 'site', 'web site', 'company website',
        'homepage', 'web address',
    ],
    'Industry': [
        'industry', 'sector', 'segment', 'industry segment', 'business sector',
        'vertical',
    ],
}

REQUIRED_CANONICAL = ['EnterpriseName']  # only company name is strictly required
RECOMMENDED_CANONICAL = ['Address', 'State', 'District', 'Pincode']


def _normalize_col_name(name):
    """Lowercase, strip, collapse whitespace, remove punctuation."""
    if name is None: return ''
    s = str(name).strip().lower()
    s = re.sub(r'[^\w\s/]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def detect_schema(df):
    """
    Returns: (mapping, warnings)
      mapping  = {input_col_name: canonical_name} for every column that matched
      warnings = list of strings about issues (missing required, ambiguous, etc.)
    """
    mapping = {}
    warnings = []

    # Build reverse index: variant → canonical
    variant_to_canonical = {}
    for canon, variants in CANONICAL_VARIANTS.items():
        for v in variants:
            variant_to_canonical[_normalize_col_name(v)] = canon

    # Match each input column
    canon_used = set()
    for col in df.columns:
        normalized = _normalize_col_name(col)
        canon = variant_to_canonical.get(normalized)
        if canon and canon not in canon_used:
            mapping[col] = canon
            canon_used.add(canon)

    # Check required + recommended
    for req in REQUIRED_CANONICAL:
        if req not in canon_used:
            # Try a looser fuzzy match — find col with required name as substring
            for col in df.columns:
                if req.lower() in _normalize_col_name(col):
                    mapping[col] = req
                    canon_used.add(req)
                    warnings.append(
                        f"Loose-matched '{col}' → '{req}' (no exact variant found)")
                    break
        if req not in canon_used:
            warnings.append(
                f"❌ REQUIRED column '{req}' not found. Input columns: {list(df.columns)}")

    for rec in RECOMMENDED_CANONICAL:
        if rec not in canon_used:
            warnings.append(f"⚠ Recommended column '{rec}' not found — will be left blank")

    return mapping, warnings


# Keywords that signal a cell contains a company name (for header-less detection)
_COMPANY_KEYWORDS = [
    'limited', 'ltd', 'pvt', 'private', 'llp', '& co', 'and co', 'company',
    'services', 'bank', 'finance', 'industries', 'corporation', 'corp',
    'enterprises', 'technologies', 'solutions', 'securities', 'capital',
    'holdings', 'ventures', 'pharma', 'systems', 'infotech', 'consultancy',
    'manufacturing', 'trading', 'exports', 'imports', 'international',
]


def _company_likeness(series):
    """Score 0+ how likely a column holds company names. Higher = more likely."""
    vals = [str(v).strip() for v in series
            if str(v).strip() and str(v).strip().lower() != 'nan']
    if not vals:
        return 0.0
    n = len(vals)
    kw_ratio  = sum(1 for v in vals if any(k in v.lower() for k in _COMPANY_KEYWORDS)) / n
    avg_len   = sum(len(v) for v in vals) / n
    uniq_ratio = len(set(vals)) / n
    # Company columns: keyword-rich, long, mostly unique
    return (kw_ratio * 3.0) + min(avg_len / 20.0, 1.5) + uniq_ratio


def _looks_like_category(series):
    """True if a column has few unique short values (a sector/category column)."""
    vals = [str(v).strip() for v in series
            if str(v).strip() and str(v).strip().lower() != 'nan']
    if not vals:
        return False
    uniq = len(set(vals))
    avg_len = sum(len(v) for v in vals) / len(vals)
    # Category: <=15 distinct values, short text (e.g. "HFC", "NBFC", "Financial Services")
    return uniq <= 15 and avg_len < 30


def detect_headerless(df):
    """
    For files with no real header (cols named Unnamed: 0/1/...), heuristically
    find the company-name column + an optional category column.

    Returns (rename_map, warnings) where rename_map maps the detected columns
    to 'EnterpriseName' (and 'Industry' if a category col is found).
    """
    rename_map, warnings = {}, []

    # Score every column for company-name-likeness
    scores = {col: _company_likeness(df[col]) for col in df.columns}
    if not scores or max(scores.values()) < 1.0:
        return {}, ['Could not auto-detect a company-name column in a header-less file']

    best_col = max(scores, key=scores.get)
    rename_map[best_col] = 'EnterpriseName'
    warnings.append(f"No header row detected — using column '{best_col}' as company name "
                    f"(auto-detected by content)")

    # Look for a category/sector column among the rest → Industry hint
    for col in df.columns:
        if col == best_col:
            continue
        if _looks_like_category(df[col]):
            rename_map[col] = 'Industry'
            warnings.append(f"Using column '{col}' as Industry/sector (category values detected)")
            break

    return rename_map, warnings


def normalize_dataframe(df):
    """
    Rename input columns to canonical names. Add empty columns for missing ones.
    Falls back to content-based detection for header-less files.

    Returns: (normalized_df, mapping, warnings)
    """
    mapping, warnings = detect_schema(df)

    # If we didn't find a company-name column via headers, try header-less detection
    if 'EnterpriseName' not in mapping.values():
        hl_map, hl_warnings = detect_headerless(df)
        if hl_map:
            mapping.update(hl_map)
            warnings = [w for w in warnings if not w.startswith('❌')]  # clear the fail
            warnings.extend(hl_warnings)

    # Rename
    df = df.rename(columns=mapping)

    # Add empty cols for missing canonical fields so downstream code doesn't crash
    for canon in CANONICAL_VARIANTS.keys():
        if canon not in df.columns:
            df[canon] = ''

    return df, mapping, warnings


if __name__ == '__main__':
    # Quick test on a variety of column-name spellings
    import pandas as pd
    samples = [
        # Standard
        pd.DataFrame({'EnterpriseName':[1], 'Address':[1], 'State':[1],
                      'District':[1], 'Pincode':[1]}),
        # Common variants
        pd.DataFrame({'Company Name':[1], 'Reg Office':[1], 'City':[1],
                      'Pin Code':[1], 'State Name':[1]}),
        # Loose/weird
        pd.DataFrame({'Organization':[1], 'Full Address':[1], 'Town':[1],
                      'Zip':[1]}),
        # Missing required col
        pd.DataFrame({'Address':[1], 'City':[1]}),
    ]
    for i, df in enumerate(samples, 1):
        print(f'\n--- Test {i} ---')
        print(f'Input cols: {list(df.columns)}')
        ndf, mapping, warnings = normalize_dataframe(df.copy())
        print(f'Mapped: {mapping}')
        print(f'Final cols: {list(ndf.columns)}')
        for w in warnings:
            print(f'  {w}')
