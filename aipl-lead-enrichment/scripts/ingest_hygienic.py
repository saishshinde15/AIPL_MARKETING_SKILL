"""
ingest_hygienic.py
==================
Pour a team-built "hygienic" contact DB (real names + real emails) into the
local cache — so its verified emails are reused and its per-domain email
PATTERNS are learned. This is Layer 0 of the v8.2 email workflow: the team's
own manual data becomes the seed/brain that powers everything downstream.

🔴 STRUCTURE-AGNOSTIC BY DESIGN. The team's files change shape every time
(2-col list one week, 11-col DB with renamed/typo'd headers the next:
"Mail id", "Concern Person Name", "Desgination"). So we do NOT trust header
names — we detect each column by its CONTENT:
  - email column  = the column whose cells actually contain @-addresses
  - name column   = the column whose cells look like person names
  - title column  = the column whose cells look like job designations
  - company column= schema_detector hint, else company-suffix likeness
  - phone columns = cells that are mostly digits
A file with no email column (a raw company list like the HFC file) simply
ingests nothing — correct, there's nothing to learn.

USAGE:
    from ingest_hygienic import ingest_file
    report = ingest_file("Insurance DB 02.06.26.xlsx", sheet="Database")
    # → {'emails_ingested': 190, 'patterns_learned': 69, 'domains': [...], ...}

Patterns/emails land in ~/.aipl-cache (keyed by company + domain), independent
of any file's layout. The cache is the durable asset; every file is transient.
"""
import re
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    pd = None

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_HONORIFICS = {"mr", "mr.", "ms", "ms.", "mrs", "mrs.", "dr", "dr.", "m/s", "shri", "smt"}
_TITLE_KW = (
    "cto", "cio", "ciso", "cdo", "manager", "head", "director", "officer",
    "president", "vp", "vice president", "lead", "chief", "infra", "executive",
    "gm", "dgm", "agm", "analyst", "engineer", "consultant", "secretary",
    "administrator", "admin", "incharge", "in-charge", "specialist", "architect",
    "coordinator", "supervisor", "avp", "svp", "evp", "owner", "proprietor",
    "partner", "founder", "ceo", "coo", "cfo", "md", "technology", "digital",
    "information", "systems", "security", "it ", " it", "edp", "network",
)
_COMPANY_SFX = ("limited", "ltd", "pvt", "private", "llp", "& co", "and co",
                "company", "corporation", "industries", "enterprises", "insurance",
                "finance", "bank", "services", "technologies", "solutions")


def _cells(series):
    return [str(v).strip() for v in series if v is not None and str(v).strip()
            and str(v).strip().lower() != "nan"]


def _email_score(series):
    c = _cells(series)
    if not c:
        return 0.0
    return sum(1 for v in c if _EMAIL_RE.search(v)) / len(c)


def _name_score(series):
    """Looks like person names: 2–4 alpha tokens AND high distinct-value cardinality.
    The cardinality guard kills repeated-category columns ("Financial", "Mumbai")
    that would otherwise look name-like as single words."""
    c = _cells(series)
    if not c:
        return 0.0
    card = len(set(v.lower() for v in c)) / len(c)
    if card < 0.30:                      # few distinct values => a category, not names
        return 0.0
    hits = 0
    for v in c:
        if "@" in v or any(ch.isdigit() for ch in v):
            continue
        toks = [t for t in re.split(r"\s+", v) if t]
        toks = [t for t in toks if t.lower().strip(".") not in _HONORIFICS]
        if 2 <= len(toks) <= 4 and all(re.fullmatch(r"[A-Za-z][A-Za-z.'-]*", t) for t in toks):
            hits += 1
    return hits / len(c)


def _title_score(series):
    c = _cells(series)
    if not c:
        return 0.0
    return sum(1 for v in c if any(k in v.lower() for k in _TITLE_KW)) / len(c)


def _company_score(series):
    c = _cells(series)
    if not c:
        return 0.0
    return sum(1 for v in c if any(s in v.lower() for s in _COMPANY_SFX)) / len(c)


def _phone_score(series):
    c = _cells(series)
    if not c:
        return 0.0
    hits = 0
    for v in c:
        if "@" in v or len(v) > 40:        # long cells = addresses, not phones
            continue
        digits = re.sub(r"\D", "", v)
        if 7 <= len(digits) <= 12:
            hits += 1
    return hits / len(c)


def detect_contact_columns(df):
    """Content-based detection. Returns {role: column_name} for whatever exists."""
    cols = list(df.columns)
    scored = {col: {
        "email": _email_score(df[col]),
        "name":  _name_score(df[col]),
        "title": _title_score(df[col]),
        "company": _company_score(df[col]),
        "phone": _phone_score(df[col]),
    } for col in cols}

    def pick(metric, threshold, exclude=()):
        best, bestv = None, threshold
        for col in cols:
            if col in exclude:
                continue
            if scored[col][metric] > bestv:
                best, bestv = col, scored[col][metric]
        return best

    email_col = pick("email", 0.25)
    company_col = pick("company", 0.30, exclude={email_col})
    # name column: highest name-score that isn't the company or email col
    name_col = pick("name", 0.40, exclude={email_col, company_col})
    title_col = pick("title", 0.30, exclude={email_col, company_col, name_col})
    phone_cols = [c for c in cols if c not in {email_col, company_col, name_col, title_col}
                  and scored[c]["phone"] > 0.40]
    return {"email": email_col, "company": company_col, "name": name_col,
            "title": title_col, "phones": phone_cols, "_scores": scored}


def _split_name(full):
    toks = [t for t in re.split(r"\s+", re.sub(r"[^A-Za-z .'-]", " ", str(full))) if t]
    toks = [t for t in toks if t.lower().strip(".") not in _HONORIFICS]
    if not toks:
        return "", ""
    if len(toks) == 1:
        return toks[0], ""
    return toks[0], toks[-1]


def ingest_df(df, cache=None, company_fallback=""):
    """Ingest a DataFrame of hygienic contacts into the cache. Returns a report."""
    sys.path.insert(0, str(Path(__file__).parent))
    from local_cache import Cache
    cache = cache or Cache()

    det = detect_contact_columns(df)
    if not det["email"] or not det["name"]:
        return {"emails_ingested": 0, "patterns_learned": 0, "domains": [],
                "detected": det, "note": "no email+name columns found — nothing to ingest "
                                          "(this is correct for a raw company list)"}

    patterns_before = cache.stats().get("email_patterns", 0)
    ingested, domains = 0, set()
    for _, row in df.iterrows():
        email = ""
        for m in [_EMAIL_RE.search(str(row[det["email"]]))]:
            if m:
                email = m.group(0).strip().lower()
        if not email:
            continue
        first, last = _split_name(row[det["name"]])
        if not (first or last):
            continue
        company = (str(row[det["company"]]).strip() if det["company"] else "") or company_fallback
        if not company or company.lower() == "nan":
            continue
        contact = {
            "first": first, "last": last, "email": email,
            "designation": (str(row[det["title"]]).strip() if det["title"] else ""),
            "confidence": "High",
            "source_url": "team hygienic DB (manual)",
            "notes": "ingested from team-built hygienic DB",
        }
        if det["phones"]:
            ph = [re.sub(r"\s+", " ", str(row[c]).strip()) for c in det["phones"]
                  if str(row[c]).strip() and str(row[c]).strip().lower() != "nan"]
            if ph:
                contact["mobile"] = ph[0]
                if len(ph) > 1:
                    contact["company_phone"] = ph[1]
        if cache.save_contact(company, contact, verified_by_team=True):
            ingested += 1
            domains.add(email.split("@", 1)[1])
    patterns_after = cache.stats().get("email_patterns", 0)
    return {
        "emails_ingested": ingested,
        "patterns_learned": patterns_after,           # total in cache now
        "patterns_new_this_run": patterns_after - patterns_before,
        "distinct_domains": len(domains),
        "detected_columns": {k: det[k] for k in ("company", "name", "email", "title", "phones")},
    }


def ingest_file(path, sheet=None, cache=None):
    if pd is None:
        raise RuntimeError("pandas required")
    xls = pd.ExcelFile(path)
    sheet = sheet or _pick_richest_sheet(xls)
    df = xls.parse(sheet)
    return ingest_df(df, cache=cache)


def _pick_richest_sheet(xls):
    """Choose the sheet most likely to hold contacts (has an email-bearing column)."""
    best, bestv = xls.sheet_names[0], -1
    for sn in xls.sheet_names:
        try:
            df = xls.parse(sn, nrows=60)
        except Exception:
            continue
        v = max([_email_score(df[c]) for c in df.columns], default=0)
        if v > bestv:
            best, bestv = sn, v
    return best


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--sheet", default=None)
    args = ap.parse_args()
    rep = ingest_file(args.path, sheet=args.sheet)
    import json
    print(json.dumps(rep, indent=2, default=str))
