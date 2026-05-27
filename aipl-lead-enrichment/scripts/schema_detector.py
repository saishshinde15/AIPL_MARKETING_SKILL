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
    'EnterpriseName': [
        'enterprisename', 'enterprise name', 'enterprise',
        'company', 'company name', 'companyname',
        'organisation', 'organization', 'organisation name', 'organization name',
        'name', 'name of company', 'name of business', 'name of organization',
        'firm', 'firm name', 'business', 'business name', 'entity', 'entity name',
        'company/firm', 'co name', 'co. name',
    ],
    'Address': [
        'address', 'office address', 'registered address', 'registered office',
        'registered office address', 'address of business', 'business address',
        'street', 'street address', 'location', 'full address', 'reg office',
        'reg. office', 'reg address', 'office', 'building address',
    ],
    'State': [
        'state', 'state name', 'province', 'region',
    ],
    'District': [
        'district', 'district name', 'city', 'city name', 'town', 'taluka',
        'place', 'city/district',
    ],
    'Pincode': [
        'pincode', 'pin code', 'pin', 'postal code', 'zip', 'zip code',
        'postal', 'postcode', 'zipcode', 'pin no', 'pin number',
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


def normalize_dataframe(df):
    """
    Rename input columns to canonical names. Add empty columns for missing ones.

    Returns: (normalized_df, mapping, warnings)
    """
    mapping, warnings = detect_schema(df)

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
