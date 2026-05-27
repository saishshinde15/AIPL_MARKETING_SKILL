"""
sales_priority.py
=================
Hot / Warm / Cold scoring for AIPL sales prioritization.

Tags each enriched company with a priority tier based on:
- Company size signals (PSU/listed > Pvt Ltd > LLP > Cooperative)
- Industry fit (IT/Finance/Manufacturing = better for IT/networking sales)
- Contact role (IT-specific > Director > unknown)
- Data completeness (have email + phone = more actionable)

Pure Python, zero LLM calls. Runs in <1 ms per row.

USAGE:
    from sales_priority import score
    tier, reason = score(row)
    # → ('Hot', 'Listed large enterprise + IT-specific contact + email + phone')
"""
import re

# ---- Industry fit weights (higher = better for AIPL's IT/networking pitch) ----
INDUSTRY_FIT = {
    'Financial Services':  9,  # banks/NBFCs spend heavily on IT
    'IT & Software':       8,  # they buy from peers
    'Manufacturing':       8,  # industrial IT/networking needs
    'Oil & Gas':          10,  # very heavy IT spenders (PSUs)
    'Pharmaceuticals':     8,
    'Logistics & Shipping':7,
    'Construction & Infra':6,
    'Travel & Hospitality':5,
    'Real Estate':         4,
    'Agriculture':         3,
    'Cooperative Society': 1,
    'NBFC / Nidhi':        2,
    '':                    4,  # unknown — middling default
}

# ---- Company size signals from the name itself ----
LARGE_PSU_KEYWORDS = [
    'CORPORATION LIMITED', 'CORPORATION LTD', 'OIL AND NATURAL GAS', 'ONGC',
    'NTPC', 'BHEL', 'SAIL', 'GAIL', 'IOCL', 'BARODA', 'STATE BANK',
    'BANK OF', 'INDIA POST', 'AIRPORTS AUTHORITY',
]
LISTED_LIKELY = [
    'MOTILAL OSWAL', 'ANAND RATHI', 'HAZOOR', 'INDISTOCK',
    'MANUGRAPH', 'BATLIBOI', 'CHEMBOND', 'TARAPUR TRANSFORMERS',
    'APLAB', 'SKY INDUSTRIES', 'HINDWARE',
]
MID_SIZE_SIGNALS = ['LIMITED', ' LTD']  # listed/public companies likely mid-size+
SMALL_SIGNALS = ['PRIVATE LIMITED', 'PVT LTD', 'PVT. LTD', 'PVT LIMITED']
TINY_SIGNALS = ['LIMITED LIABILITY PARTNERSHIP', ' LLP']
SKIP_SIGNALS = ['SAHAKARI', 'PATSANTHA', 'NIDHI', 'PRODUCER COMPANY']

# IT-decision-maker role priority
IT_ROLES = {
    'VP IT / CISO / CTO':       10,
    'IT Manager / IT Head':      8,
    'IT Infra / Sr. IT Infra':   7,
    'IT Procurement / Purchase': 6,
}

GATEKEEPER_ROLES = {
    'Gatekeeper - Managing Director': 4,
    'Gatekeeper - Chairman & MD':     4,
    'Gatekeeper - CEO':               4,
    'Gatekeeper - Director':          3,
    'Gatekeeper - Chairman':          3,
    'Gatekeeper - Founder':           3,
    'Gatekeeper - Partner':           2,
    'Gatekeeper - Unknown Role':      1,
}


def _size_score(company_name):
    """Heuristic company-size score from the name. 1 (tiny) — 10 (mega)."""
    up = (company_name or '').upper()
    if any(k in up for k in SKIP_SIGNALS):
        return 0
    if any(k in up for k in LARGE_PSU_KEYWORDS):
        return 10
    if any(k in up for k in LISTED_LIKELY):
        return 8
    if any(k in up for k in TINY_SIGNALS):
        return 3
    if any(k in up for k in SMALL_SIGNALS):
        return 4
    if any(k in up for k in MID_SIZE_SIGNALS):
        return 6  # plain "Limited" = listed/public, likely mid-size+
    return 4  # default


def _role_score(designation):
    """Score the contact's role."""
    if not designation:
        return 0
    if designation in IT_ROLES:
        return IT_ROLES[designation]
    if designation in GATEKEEPER_ROLES:
        return GATEKEEPER_ROLES[designation]
    return 1  # unknown title


def _data_completeness(row):
    """Bonus for actionable data (email + phone)."""
    has_email = bool(str(row.get('Primary Email','')).strip())
    has_phone = bool(str(row.get('Office Phone','')).strip()
                     or str(row.get('Mobile Phone','')).strip())
    return (3 if has_email else 0) + (3 if has_phone else 0)


def score(row):
    """
    Returns (tier, reason) where:
      tier   = 'Hot' / 'Warm' / 'Cold' / 'Skip'
      reason = short explanation of the rating
    """
    company  = str(row.get('Company',''))
    industry = str(row.get('Industry',''))
    desg     = str(row.get('Designation',''))

    size  = _size_score(company)
    fit   = INDUSTRY_FIT.get(industry, 4)
    role  = _role_score(desg)
    data  = _data_completeness(row)

    # If company is a Sahakari / Nidhi / Producer Co, just skip
    if size == 0:
        return ('Skip', f'Cooperative / Nidhi / Producer Company — low fit for IT sales')

    total = size + fit + role + data  # 0–35

    if total >= 25:
        tier = 'Hot'
    elif total >= 16:
        tier = 'Warm'
    else:
        tier = 'Cold'

    # Build a human-readable reason
    bits = []
    if size >= 8: bits.append('large enterprise')
    elif size >= 6: bits.append('mid-size')
    elif size >= 4: bits.append('small Pvt Ltd')
    else: bits.append('micro/LLP')

    if fit >= 8: bits.append('high-IT-spend industry')
    elif fit >= 6: bits.append('decent industry fit')

    if role >= 8: bits.append('IT decision-maker found')
    elif role >= 4: bits.append('gatekeeper found')
    elif role >= 1: bits.append('contact found (role unclear)')
    else: bits.append('no contact yet')

    if data >= 6: bits.append('email + phone in hand')
    elif data >= 3: bits.append('partial contact info')
    else: bits.append('no email/phone')

    return (tier, ' + '.join(bits) + f' (score: {total}/35)')


if __name__ == '__main__':
    # Self-test
    cases = [
        {'Company':'OIL AND NATURAL GAS CORPORATION LIMITED', 'Industry':'Oil & Gas',
         'Designation':'VP IT / CISO / CTO', 'Primary Email':'cio@ongc.co.in',
         'Office Phone':'+91-22-2627-7000', 'Mobile Phone':''},
        {'Company':'M/S MAGBLISS INFOTECH PRIVATE LIMITED', 'Industry':'IT & Software',
         'Designation':'Gatekeeper - Director', 'Primary Email':'', 'Office Phone':'', 'Mobile Phone':''},
        {'Company':'PUNE ZILLANAGARI SAHAKARI PATSANTHA FEDRATION LTD',
         'Industry':'Cooperative Society', 'Designation':'IT Manager / IT Head',
         'Primary Email':'', 'Office Phone':'', 'Mobile Phone':''},
        {'Company':'Motilal Oswal Financial Services Ltd', 'Industry':'Financial Services',
         'Designation':'IT Manager / IT Head', 'Primary Email':'pankaj.purohit@motilaloswal.com',
         'Office Phone':'+91-22-7193-4263', 'Mobile Phone':''},
    ]
    for c in cases:
        t, r = score(c)
        print(f"{t:5s} | {c['Company'][:45]:<45} → {r}")
