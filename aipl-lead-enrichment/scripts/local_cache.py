"""
local_cache.py
==============
SQLite-backed contact cache for the AIPL lead enrichment skill.

This is the FLYWHEEL — every contact the team ever verifies (web research,
LinkedIn lookup, Lusha/Apollo unlock, switchboard call) gets stored here.
Future runs check the cache FIRST before doing any new research.

After 6 months of weekly runs, the cache becomes a meaningful first-party
Indian SME contact database that no paid tool has.

DESIGN:
- Zero external dependencies (pure stdlib sqlite3)
- Cache lives at ~/.aipl-cache/contacts.db (per-user, not in the repo)
- Schema is versioned + migrates forward automatically
- "Soft TTL" — cached contacts older than 180 days get re-verified
  (job changes happen)

USAGE:
    from local_cache import Cache
    c = Cache()                                              # opens / creates
    hit = c.lookup_company("Motilal Oswal Financial Services")  # → dict or None
    c.save_contact("Motilal Oswal Financial Services", {     # save what we find
        'first': 'Pankaj', 'last': 'Purohit',
        'designation': 'EVP & Head IT',
        'email': 'pankaj.purohit@motilaloswal.com',
        'phone': '+91-22-7193-4263', 'mobile': '',
        'source_url': 'https://linkedin.com/in/pankaj-purohit',
        'confidence': 'High',
    })
    c.learn_email_pattern("motilaloswal.com", "first.last")  # learn from confirmed
    c.stats()                                                # → coverage summary
"""
import sqlite3
import os
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

CACHE_DIR = Path.home() / ".aipl-cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = CACHE_DIR / "contacts.db"

# Bump this number when adding columns; migration runs automatically.
SCHEMA_VERSION = 2

# Soft TTL: cached entries older than this are flagged stale, but still returned
# (so the team has SOMETHING to call). The skill can decide whether to refresh.
STALE_AFTER_DAYS = 180


def _norm_company(name):
    """Canonical key for fuzzy matching company names across spellings."""
    if not name:
        return ""
    n = str(name).upper().strip()
    # Drop common Indian co suffixes for matching
    for sfx in ["M/S ", "PRIVATE LIMITED", "PVT. LTD", "PVT LTD",
                "PVT LIMITED", "LIMITED", " LTD", " LLP",
                "LIABILITY PARTNERSHIP", "(INDIA)", ".", ","]:
        n = n.replace(sfx, " ")
    return re.sub(r"\s+", " ", n).strip()


class Cache:
    def __init__(self, db_path=None):
        self.db_path = db_path or str(DB_PATH)
        self._db = sqlite3.connect(self.db_path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode = WAL")
        self._migrate()

    # ---- Schema ----
    def _migrate(self):
        c = self._db.cursor()
        # meta table for version tracking
        c.execute("""
            CREATE TABLE IF NOT EXISTS _meta (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        c.execute("SELECT value FROM _meta WHERE key='schema_version'")
        row = c.fetchone()
        current = int(row["value"]) if row else 0

        if current < 1:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS companies (
                    norm_name      TEXT PRIMARY KEY,   -- normalized matching key
                    display_name   TEXT NOT NULL,      -- pretty name (last seen)
                    cin            TEXT,
                    industry       TEXT,
                    website        TEXT,
                    registered_address TEXT,
                    city           TEXT,
                    state          TEXT,
                    pincode        TEXT,
                    first_seen     TEXT NOT NULL,
                    last_updated   TEXT NOT NULL,
                    sources        TEXT                -- JSON list of source URLs
                );

                CREATE TABLE IF NOT EXISTS contacts (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    norm_company    TEXT NOT NULL,
                    first_name      TEXT,
                    last_name       TEXT,
                    designation     TEXT,
                    email           TEXT,
                    phone           TEXT,              -- office / switchboard
                    mobile          TEXT,
                    linkedin        TEXT,
                    source_url      TEXT,
                    confidence      TEXT,              -- High / Medium / Low
                    notes           TEXT,
                    first_seen      TEXT NOT NULL,
                    last_verified   TEXT NOT NULL,     -- updated on every re-confirm
                    verified_by_team INTEGER DEFAULT 0, -- 1 if team confirmed by calling
                    FOREIGN KEY (norm_company) REFERENCES companies(norm_name)
                );

                CREATE TABLE IF NOT EXISTS email_patterns (
                    domain          TEXT PRIMARY KEY,  -- e.g. "motilaloswal.com"
                    pattern         TEXT NOT NULL,     -- e.g. "first.last"
                    confidence      TEXT NOT NULL,     -- High = 2+ samples, Medium = 1
                    sample_count    INTEGER DEFAULT 1,
                    last_updated    TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(norm_company);
                CREATE INDEX IF NOT EXISTS idx_contacts_email   ON contacts(email);
                CREATE INDEX IF NOT EXISTS idx_companies_city   ON companies(city);
            """)
            c.execute("INSERT OR REPLACE INTO _meta (key, value) VALUES ('schema_version', '1')")

        # ---- Schema v2: company-switchboard + IT-department phone backups ----
        # (v7.7.2) Without these, the cache silently dropped the switchboard +
        # IT-dept numbers on every repeat run, halving phone coverage weekly.
        if current < 2:
            existing_cols = {r[1] for r in c.execute("PRAGMA table_info(contacts)")}
            if 'company_phone' not in existing_cols:
                c.execute("ALTER TABLE contacts ADD COLUMN company_phone TEXT")
            if 'it_phone' not in existing_cols:
                c.execute("ALTER TABLE contacts ADD COLUMN it_phone TEXT")
            c.execute("INSERT OR REPLACE INTO _meta (key, value) VALUES ('schema_version', '2')")

        self._db.commit()

    # ---- Company lookup ----
    def lookup_company(self, name):
        """Return dict for cached company + its contacts, or None."""
        key = _norm_company(name)
        if not key:
            return None
        c = self._db.cursor()
        c.execute("SELECT * FROM companies WHERE norm_name = ?", (key,))
        co = c.fetchone()
        if not co:
            return None
        c.execute("""
            SELECT * FROM contacts WHERE norm_company = ?
            ORDER BY verified_by_team DESC,
                     CASE confidence WHEN 'High' THEN 0
                                     WHEN 'Medium' THEN 1
                                     ELSE 2 END,
                     last_verified DESC
        """, (key,))
        contacts = [dict(r) for r in c.fetchall()]

        # Compute staleness
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for ct in contacts:
            try:
                last = datetime.fromisoformat(ct["last_verified"])
                ct["is_stale"] = (now - last) > timedelta(days=STALE_AFTER_DAYS)
                ct["days_old"] = (now - last).days
            except (ValueError, TypeError):
                ct["is_stale"] = True
                ct["days_old"] = 9999

        return {
            "company":  dict(co),
            "contacts": contacts,
            "best":     contacts[0] if contacts else None,  # already sorted by priority
        }

    # ---- Save / upsert ----
    def save_company(self, name, **fields):
        """Upsert a company record. Returns the normalized key."""
        key = _norm_company(name)
        if not key:
            return None
        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
        c = self._db.cursor()
        c.execute("SELECT first_seen, sources FROM companies WHERE norm_name = ?", (key,))
        existing = c.fetchone()

        # Merge sources list
        new_source = fields.pop("source_url", None)
        existing_sources = []
        if existing and existing["sources"]:
            try:
                existing_sources = json.loads(existing["sources"])
            except json.JSONDecodeError:
                pass
        if new_source and new_source not in existing_sources:
            existing_sources.append(new_source)

        params = {
            "norm_name":          key,
            "display_name":       str(name).strip(),
            "cin":                fields.get("cin", ""),
            "industry":           fields.get("industry", ""),
            "website":            fields.get("website", ""),
            "registered_address": fields.get("address", ""),
            "city":               fields.get("city", ""),
            "state":              fields.get("state", ""),
            "pincode":            fields.get("pincode", ""),
            "first_seen":         (existing["first_seen"] if existing else now),
            "last_updated":       now,
            "sources":            json.dumps(existing_sources),
        }
        c.execute("""
            INSERT OR REPLACE INTO companies
              (norm_name, display_name, cin, industry, website, registered_address,
               city, state, pincode, first_seen, last_updated, sources)
            VALUES (:norm_name, :display_name, :cin, :industry, :website, :registered_address,
                    :city, :state, :pincode, :first_seen, :last_updated, :sources)
        """, params)
        self._db.commit()
        return key

    def save_contact(self, company_name, contact, verified_by_team=False):
        """
        Add or update a contact for a company.
        Dedupe on (company, email) or (company, first+last). Updates last_verified.
        """
        key = _norm_company(company_name)
        if not key:
            return False
        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
        first  = (contact.get("first") or contact.get("first_name") or "").strip()
        last   = (contact.get("last")  or contact.get("last_name")  or "").strip()
        email  = (contact.get("email") or "").strip().lower()

        # v7.2 GUARD: only cache contacts that have a NAME.
        # An email/phone with no person attached is NOT a useful "contact" — and
        # caching nameless records pollutes the cache (it can become the "best"
        # hit and wipe real names). A contact must identify a person.
        if not (first or last):
            return False

        # Ensure parent company row exists
        c = self._db.cursor()
        c.execute("SELECT 1 FROM companies WHERE norm_name = ?", (key,))
        if not c.fetchone():
            self.save_company(company_name)

        # Look for an existing match: same email, or same first+last name
        if email:
            c.execute("SELECT id, first_seen FROM contacts WHERE norm_company = ? AND email = ?",
                      (key, email))
        else:
            c.execute("SELECT id, first_seen FROM contacts WHERE norm_company = ? "
                      "AND first_name = ? AND last_name = ?",
                      (key, first, last))
        existing = c.fetchone()

        params = {
            "norm_company":   key,
            "first_name":     first,
            "last_name":      last,
            "designation":    (contact.get("designation") or "").strip(),
            "email":          email,
            "phone":          (contact.get("phone")  or "").strip(),
            "mobile":         (contact.get("mobile") or "").strip(),
            # v7.7.2: persist the switchboard + IT-dept backups so they survive
            # repeat runs (was the root cause of phone coverage halving on rebuild)
            "company_phone":  (contact.get("company_phone") or "").strip(),
            "it_phone":       (contact.get("it_phone") or "").strip(),
            "linkedin":       (contact.get("linkedin") or "").strip(),
            "source_url":     (contact.get("source_url") or "").strip(),
            "confidence":     (contact.get("confidence") or "").strip(),
            "notes":          (contact.get("notes") or "").strip()[:500],
            "first_seen":     (existing["first_seen"] if existing else now),
            "last_verified":  now,
            "verified_by_team": 1 if verified_by_team else 0,
        }
        if existing:
            params["id"] = existing["id"]
            c.execute("""
                UPDATE contacts SET
                    first_name = :first_name, last_name = :last_name,
                    designation = :designation, email = :email,
                    phone = :phone, mobile = :mobile,
                    company_phone = COALESCE(NULLIF(:company_phone,''), company_phone),
                    it_phone = COALESCE(NULLIF(:it_phone,''), it_phone),
                    linkedin = :linkedin,
                    source_url = :source_url, confidence = :confidence,
                    notes = :notes, last_verified = :last_verified,
                    verified_by_team = MAX(verified_by_team, :verified_by_team)
                WHERE id = :id
            """, params)
        else:
            c.execute("""
                INSERT INTO contacts (norm_company, first_name, last_name, designation,
                    email, phone, mobile, company_phone, it_phone, linkedin, source_url,
                    confidence, notes, first_seen, last_verified, verified_by_team)
                VALUES (:norm_company, :first_name, :last_name, :designation,
                    :email, :phone, :mobile, :company_phone, :it_phone, :linkedin,
                    :source_url, :confidence, :notes, :first_seen, :last_verified,
                    :verified_by_team)
            """, params)
        self._db.commit()

        # If email + domain match, learn the pattern
        if email and "@" in email:
            local, _, domain = email.partition("@")
            self._infer_and_save_pattern(domain, first, last, local)
        return True

    def _infer_and_save_pattern(self, domain, first, last, local):
        """Detect which permutation produced this email; record it."""
        if not (first and last and local):
            return
        f, l = first.lower(), last.lower()
        fl, ll = f[:1], l[:1]
        candidates = {
            "first.last":   f"{f}.{l}",
            "firstlast":    f"{f}{l}",
            "flast":        f"{fl}{l}",
            "first":        f"{f}",
            "first_last":   f"{f}_{l}",
            "last.first":   f"{l}.{f}",
            "first.l":      f"{f}.{ll}",
            "f.last":       f"{fl}.{l}",
        }
        detected = None
        for name, candidate in candidates.items():
            if local.lower() == candidate:
                detected = name
                break
        if not detected:
            return
        self.learn_email_pattern(domain.lower(), detected)

    def learn_email_pattern(self, domain, pattern):
        """Increase confidence in a (domain, pattern) mapping."""
        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
        c = self._db.cursor()
        c.execute("SELECT pattern, sample_count FROM email_patterns WHERE domain = ?", (domain,))
        row = c.fetchone()
        if row and row["pattern"] == pattern:
            new_count = row["sample_count"] + 1
            conf = "High" if new_count >= 2 else "Medium"
            c.execute("""UPDATE email_patterns SET sample_count = ?,
                         confidence = ?, last_updated = ? WHERE domain = ?""",
                      (new_count, conf, now, domain))
        elif row:
            # Conflict — different pattern detected. Reset to Medium with sample=1.
            c.execute("""UPDATE email_patterns SET pattern = ?, sample_count = 1,
                         confidence = 'Medium', last_updated = ? WHERE domain = ?""",
                      (pattern, now, domain))
        else:
            c.execute("""INSERT INTO email_patterns
                         (domain, pattern, confidence, sample_count, last_updated)
                         VALUES (?, ?, 'Medium', 1, ?)""", (domain, pattern, now))
        self._db.commit()

    def lookup_pattern(self, domain):
        """Return (pattern, confidence) for a domain, or (None, None)."""
        c = self._db.cursor()
        c.execute("SELECT pattern, confidence FROM email_patterns WHERE domain = ?", (domain.lower(),))
        row = c.fetchone()
        return (row["pattern"], row["confidence"]) if row else (None, None)

    # ---- Stats ----
    def stats(self):
        """Return cache coverage summary."""
        c = self._db.cursor()
        c.execute("SELECT COUNT(*) AS n FROM companies")
        n_co = c.fetchone()["n"]
        c.execute("SELECT COUNT(*) AS n FROM contacts")
        n_ct = c.fetchone()["n"]
        c.execute("SELECT COUNT(*) AS n FROM contacts WHERE verified_by_team = 1")
        n_team = c.fetchone()["n"]
        c.execute("SELECT COUNT(*) AS n FROM email_patterns")
        n_pat = c.fetchone()["n"]
        c.execute("""SELECT COUNT(*) AS n FROM contacts WHERE
                     julianday('now') - julianday(last_verified) > ?""", (STALE_AFTER_DAYS,))
        n_stale = c.fetchone()["n"]
        return {
            "companies":       n_co,
            "contacts":        n_ct,
            "team_verified":   n_team,
            "email_patterns":  n_pat,
            "stale_contacts":  n_stale,
            "db_path":         self.db_path,
        }

    def close(self):
        self._db.close()


if __name__ == "__main__":
    c = Cache()
    print(f"Cache opened at {c.db_path}")
    print(f"Stats: {c.stats()}")
    # Quick smoke test
    c.save_company("Motilal Oswal Financial Services Ltd", website="https://www.motilaloswal.com",
                   city="Mumbai", state="Maharashtra")
    c.save_contact("Motilal Oswal Financial Services Ltd", {
        "first": "Pankaj", "last": "Purohit",
        "designation": "EVP & Head IT",
        "email": "pankaj.purohit@motilaloswal.com",
        "phone": "+91-22-7193-4263",
        "source_url": "https://linkedin.com/in/pankaj-purohit",
        "confidence": "High",
    })
    hit = c.lookup_company("MOTILAL OSWAL FINANCIAL SERVICES LTD")
    print(f"\nLookup test: {hit['best']['first_name']} {hit['best']['last_name']} "
          f"({hit['best']['designation']}) — stale: {hit['best']['is_stale']}")
    pat, conf = c.lookup_pattern("motilaloswal.com")
    print(f"Pattern learned: {pat} ({conf})")
    print(f"\nFinal stats: {c.stats()}")
    c.close()
