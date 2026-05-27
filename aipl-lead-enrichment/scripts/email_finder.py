"""
email_finder.py
================
Pure-Python email permutation + MX validation. Zero LLM calls.

Given a contact's first/last name + a company domain (or website URL), tries
the 8 most common B2B email patterns, validates each via DNS MX record check,
and returns the deliverable address(es) ranked by pattern popularity.

USAGE:
    from email_finder import find_email
    result = find_email("Pankaj", "Purohit", "motilaloswal.com")
    # → {"email": "pankaj.purohit@motilaloswal.com", "confidence": "Medium",
    #    "method": "MX validated, pattern=first.last", "all_tried": [...]}

NOTES:
- MX check (DNS) confirms the DOMAIN accepts mail. It does NOT confirm the
  specific mailbox exists. For mailbox-level validation we'd need SMTP probe
  (slow, often blocked).
- We return confidence as "Medium" for MX-validated guesses — better than
  Apollo's typical guess-and-pray but still not a delivery guarantee.
- Use this AFTER you have a name + a verified company website. Don't run it
  blindly — that's how you generate the same fake URLs we already removed.
"""
import re
import socket
from urllib.parse import urlparse

try:
    import dns.resolver
    _DNS_OK = True
except ImportError:
    _DNS_OK = False


# Most common B2B patterns globally (especially for Indian SMEs)
# Order matters — most-popular first so we return the most-likely match.
PATTERNS = [
    "{first}.{last}",       # pankaj.purohit
    "{first}{last}",        # pankajpurohit
    "{f}{last}",            # ppurohit
    "{first}",              # pankaj
    "{first}_{last}",       # pankaj_purohit
    "{last}.{first}",       # purohit.pankaj
    "{first}.{l}",          # pankaj.p
    "{f}.{last}",           # p.purohit
]


def _domain_from_website(website):
    """Extract just the domain (no http/www/path) from a website string."""
    if not website:
        return ""
    s = str(website).strip()
    if "@" in s:           # not a website — it's an email
        return ""
    if "://" in s:
        s = urlparse(s).netloc
    s = s.lower().lstrip("www.").split("/")[0].split("?")[0].split("(")[0].strip()
    # Reject if it doesn't look like a domain
    if not re.match(r"^[\w-]+\.[\w.-]+$", s):
        return ""
    return s


def _clean(name):
    """Lowercase + strip non-letter chars from a name part."""
    if not name:
        return ""
    return re.sub(r"[^a-z]", "", str(name).lower())


def _has_mx(domain):
    """True if the domain has an MX record (accepts mail)."""
    if not domain:
        return False
    if not _DNS_OK:
        # Fallback: try a socket connection on port 25 (less reliable)
        try:
            socket.gethostbyname(domain)
            return True
        except Exception:
            return False
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=3)
        return len(list(answers)) > 0
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout,
            dns.exception.DNSException, Exception):
        return False


def find_email(first, last, website_or_domain):
    """
    Generate candidate emails, validate the domain via MX, return best guess.

    Returns dict:
        {'email': str, 'confidence': str, 'method': str, 'all_tried': [str], 'mx_ok': bool}
    Or empty {} if no domain or MX fails.
    """
    domain = _domain_from_website(website_or_domain)
    if not domain:
        return {}

    mx_ok = _has_mx(domain)
    if not mx_ok:
        return {"email": "", "confidence": "NOT_FOUND",
                "method": f"Domain {domain} has no MX record (rejects mail)",
                "all_tried": [], "mx_ok": False}

    f = _clean(first)
    l = _clean(last)
    if not f and not l:
        return {}

    fl = f[:1] if f else ""
    ll = l[:1] if l else ""

    tried = []
    for pat in PATTERNS:
        local = pat.format(first=f, last=l, f=fl, l=ll)
        # Skip patterns that don't produce a valid local-part
        local = local.strip(".-_")
        if not local or len(local) < 2:
            continue
        addr = f"{local}@{domain}"
        if addr not in tried:
            tried.append(addr)

    # Without per-mailbox SMTP probe, we can't pick THE right one from MX alone.
    # Return the first pattern (most common: first.last@) as Medium confidence,
    # plus the full list so the team can also try alternatives if needed.
    if not tried:
        return {}

    return {
        "email":      tried[0],
        "confidence": "Medium",
        "method":     f"MX-validated domain ({domain}); pattern=first.last",
        "all_tried":  tried,
        "mx_ok":      True,
    }


def find_email_with_smtp_probe(first, last, website_or_domain, timeout=5):
    """
    Stricter version: MX check + SMTP HELO/RCPT probe to confirm the specific
    mailbox accepts mail. Slower (5-10 sec per address) and sometimes blocked
    by anti-spam systems, but much more confident.

    Returns same dict shape but with confidence="High" if probe succeeded.
    """
    base = find_email(first, last, website_or_domain)
    if not base or not base.get("mx_ok"):
        return base

    domain = _domain_from_website(website_or_domain)

    try:
        import smtplib
        # Get the actual MX server
        if _DNS_OK:
            mx_records = dns.resolver.resolve(domain, "MX", lifetime=3)
            mx_host = str(sorted(mx_records, key=lambda r: r.preference)[0].exchange).rstrip(".")
        else:
            mx_host = domain

        # Try each candidate; return the first one the server accepts
        for addr in base["all_tried"]:
            try:
                with smtplib.SMTP(mx_host, 25, timeout=timeout) as smtp:
                    smtp.helo("aipl-enrichment.local")
                    smtp.mail("verify@aipl-enrichment.local")
                    code, _ = smtp.rcpt(addr)
                    if code in (250, 251):
                        return {
                            "email":      addr,
                            "confidence": "High",
                            "method":     f"MX + SMTP RCPT verified (code {code})",
                            "all_tried":  base["all_tried"],
                            "mx_ok":      True,
                        }
            except (smtplib.SMTPException, socket.timeout, OSError):
                continue
    except Exception as e:
        # SMTP probe failed entirely (firewall, etc.) — fall back to MX-only result
        base["method"] += f"; SMTP probe failed: {type(e).__name__}"

    return base


if __name__ == "__main__":
    # Quick self-test
    tests = [
        ("Pankaj", "Purohit", "motilaloswal.com"),
        ("Bilbo",  "Baggins", "nonexistent-domain-9876xyz.com"),
        ("",       "",        "google.com"),
        ("Manoranjan", "Mahapatra", "https://www.chembondindia.com/"),
    ]
    for f, l, w in tests:
        r = find_email(f, l, w)
        print(f"{f:>12} {l:<12} @ {w[:40]:<40} → {r.get('email','—'):<50} [{r.get('confidence','—')}]")
