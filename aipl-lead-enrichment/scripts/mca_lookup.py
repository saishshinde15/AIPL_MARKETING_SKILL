"""
mca_lookup.py
=============
Optional Indian-company registry lookup. Tries OpenCorporates (legit free
tier API, requires a free signup key) and falls back to documented manual
MCA21 portal workflow.

CONFIG:
    Set environment variable AIPL_OPENCORP_KEY before invoking the skill.
    Free key (50K calls/month) is available after signup at:
      https://opencorporates.com/api_accounts/new

    Without a key, this module is a graceful no-op — the skill keeps working,
    you just lose the ~5-10% bonus coverage on brand-new Pvt Ltds.

WHY OpenCorporates (not direct MCA scraping):
- MCA21 portal is CAPTCHA-locked + ToS forbids automated lookups
- OpenCorporates legally aggregates MCA filings + publishes them via official API
- Their Indian SME coverage is ~60-70% for cos incorporated 2020-2025
- Free tier is generous enough for AIPL's volume (100 cos/week = 400/month)

USAGE:
    from mca_lookup import lookup, available
    if available():
        result = lookup("MOTILAL OSWAL FINANCIAL SERVICES LIMITED", cin="L67190MH2005PLC153397")
        # → {'cin': '...', 'status': 'Active', 'directors': [...], 'registered_address': '...'}
"""
import os
import re
import time
import json
from urllib.parse import quote_plus

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

OC_BASE = "https://api.opencorporates.com/v0.4"
ENV_KEY = "AIPL_OPENCORP_KEY"
USER_AGENT = "aipl-lead-enrichment-skill/1.0"
TIMEOUT = 15
RATE_LIMIT_DELAY_S = 1.5  # be polite even with valid key


def available():
    """True if we can actually call the API (deps + key present)."""
    return _HAS_REQUESTS and bool(os.environ.get(ENV_KEY))


def _get(path, params=None):
    """Wrap an OpenCorporates GET, returning JSON dict or {} on any failure."""
    if not available():
        return {}
    params = dict(params or {})
    params["api_token"] = os.environ[ENV_KEY]
    try:
        r = requests.get(f"{OC_BASE}{path}", params=params,
                         headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 401:
            # bad key — disable subsequent calls this session
            os.environ.pop(ENV_KEY, None)
        return {}
    except (requests.RequestException, ValueError):
        return {}


def _clean_name_for_search(name):
    """Strip suffixes that confuse OpenCorporates search."""
    if not name:
        return ""
    n = re.sub(r"\bm/s\s+", "", str(name), flags=re.IGNORECASE)
    n = re.sub(r"\(india\)", "", n, flags=re.IGNORECASE)
    n = re.sub(r"\s+", " ", n).strip(" ,.")
    return n


def lookup(company_name, cin=None):
    """
    Look up an Indian company. Returns dict (possibly empty if not found / no key).

    Result schema:
        {
          'cin':                str,
          'name':               str,
          'status':             str,                # 'Active' / 'Strike off' / etc.
          'incorporation_date': str,                # 'YYYY-MM-DD'
          'company_type':       str,                # 'Private' / 'Public' / 'LLP'
          'registered_address': str,
          'directors':          [{name, position, appointed_date, din}],
          'source_url':         str,
          'confidence':         'High',             # MCA filings are authoritative
        }
    """
    if not available():
        return {}

    # Direct CIN lookup is best — most reliable
    if cin:
        data = _get(f"/companies/in/{cin}")
        co = data.get("results", {}).get("company")
        if co:
            return _format(co)

    # Otherwise search by name
    name = _clean_name_for_search(company_name)
    if not name:
        return {}
    time.sleep(RATE_LIMIT_DELAY_S)
    data = _get("/companies/search",
                {"q": name, "jurisdiction_code": "in", "per_page": 5})
    matches = data.get("results", {}).get("companies", [])
    if not matches:
        return {}

    # Pick the best match — exact-ish name + Active status preferred
    name_upper = name.upper()
    best, best_score = None, -1
    for m in matches:
        c = m.get("company", {})
        n = (c.get("name") or "").upper()
        score = 0
        if n == name_upper:               score += 10
        elif name_upper in n or n in name_upper: score += 5
        if (c.get("current_status") or "").lower() == "active": score += 2
        if score > best_score:
            best, best_score = c, score
    if not best or best_score < 5:
        return {}

    # Officer details require a separate call
    cin = best.get("company_number")
    time.sleep(RATE_LIMIT_DELAY_S)
    od = _get(f"/companies/in/{cin}/officers")
    officers = [o.get("officer", {})
                for o in od.get("results", {}).get("officers", [])]
    best["officers"] = officers
    return _format(best)


def _format(co):
    """Normalize OC's response into our schema."""
    officers = co.get("officers", []) or []
    return {
        "cin":                co.get("company_number", ""),
        "name":               co.get("name", ""),
        "status":             co.get("current_status", ""),
        "incorporation_date": co.get("incorporation_date", ""),
        "company_type":       co.get("company_type", ""),
        "registered_address": co.get("registered_address_in_full", ""),
        "directors": [{
            "name":           o.get("name", ""),
            "position":       o.get("position", ""),
            "appointed_date": o.get("start_date", ""),
            "din":            o.get("identifiers", [{}])[0].get("identifier", "")
                                if o.get("identifiers") else "",
        } for o in officers if o.get("name")],
        "source_url": co.get("opencorporates_url", ""),
        "confidence": "High",  # registry filings are authoritative
    }


def manual_mca_url(company_name):
    """
    For when we don't have an OC key — return the URL the team should
    click + paste the name into to do the manual MCA lookup.

    Used by build_vtiger_file's MCA_LOOKUP bucket in the Coverage Report.
    """
    return ("https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do "
            "— click 'Find CIN/LLPIN' → enter company name → solve CAPTCHA → "
            "pull Director details from the master data page.")


if __name__ == "__main__":
    print(f"OpenCorporates lookup available: {available()}")
    if available():
        r = lookup("MOTILAL OSWAL FINANCIAL SERVICES LIMITED",
                   cin="L67190MH2005PLC153397")
        print(json.dumps(r, indent=2, default=str)[:1200])
    else:
        print(f"To enable: sign up at https://opencorporates.com/api_accounts/new")
        print(f"Then: export {ENV_KEY}=your_token_here")
        print(f"\nWithout the key, manual MCA workflow:")
        print(f"  {manual_mca_url('Any Company Name')}")
