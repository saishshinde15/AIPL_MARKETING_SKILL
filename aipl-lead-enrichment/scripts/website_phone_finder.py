"""
website_phone_finder.py
=======================
Extract a company's OWN published switchboard phone from its OWN website.

ETHICS: a company publishes its phone number on its Contact/About page FOR
THE WORLD TO CALL THEM. Reading that public-by-design number off the company's
own site is fine — unlike scraping third-party aggregators (JustDial/IndiaMART),
which we explicitly do NOT do. This is the GitHub-validated ethical approach
(see ericsoto-exe/ContactInfoScraper et al.).

Pure Python (requests + regex). Zero API key. Degrades gracefully:
- No internet in the sandbox? Returns {} — skill keeps working.
- Site down / no phone published? Returns {} — honest blank, no fabrication.

USAGE:
    from website_phone_finder import find_phone
    r = find_phone("https://www.batliboi.com")
    # → {'phone': '+91-22-2493-4000', 'source_url': 'https://www.batliboi.com/contact',
    #    'confidence': 'High', 'all_found': [...]}
"""
import re
from urllib.parse import urljoin, urlparse

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
TIMEOUT = 10

# Common contact-page paths to try (in priority order)
CONTACT_PATHS = ['', 'contact', 'contact-us', 'contactus', 'contact_us',
                 'about', 'about-us', 'aboutus', 'reach-us', 'get-in-touch',
                 'connect', 'corporate', 'enquiry']

# ---- Indian phone patterns ----
# Landline:  022-12345678 / +91 22 1234 5678 / (022) 2345 6789 / 0124-4567890
# Mobile:    +91 98765 43210 / 9876543210 / +91-9876543210
# Toll-free: 1800-123-4567 / 1800 123 456
_PHONE_CANDIDATE = re.compile(r'''
    (?<![\d/])                                  # not preceded by digit or slash (avoid CINs)
    (?:
        (?:\+?91[\-\s.]?)?                       # optional +91
        (?:\(?0?\d{2,4}\)?[\-\s.]?)?             # optional STD code (with optional 0/parens)
        \d{3}[\-\s.]?\d{3,4}[\-\s.]?\d{0,4}      # the number body
        |
        1800[\-\s.]?\d{3}[\-\s.]?\d{3,4}         # toll-free 1800
    )
    (?![\d])                                     # not followed by another digit
''', re.VERBOSE)


# Valid Indian landline STD-code first-digits. Codes are 2-4 digits; the first
# digit is 1-8 (mobiles use 6-9 for the WHOLE number; STD codes never start 0/9).
# 2-digit metro codes: 11/20/22/33/40/44/79/80. 3-4 digit codes start 1-8.
_VALID_2DIGIT_STD = {'11','20','22','33','40','44','79','80'}

def _normalize(raw, had_structure=False):
    """
    Clean + validate an Indian phone candidate.
    `had_structure` = the raw had +91 / leading 0 / parens / tel: (so a landline
    interpretation is trustworthy). Bare digit runs only qualify as mobiles.
    Returns formatted string or '' if invalid.
    """
    digits = re.sub(r'\D', '', raw)
    core = digits
    if core.startswith('91') and len(core) > 10:
        had_structure = True
        core = core[2:]
    if core.startswith('0'):
        had_structure = True
    core = core.lstrip('0')

    # Mobile: 10 digits starting 6-9 (always trustworthy regardless of structure)
    if len(core) == 10 and core[0] in '6789':
        return f'+91-{core[:5]}-{core[5:]}'

    # Toll-free 1800
    if digits.startswith('1800') and len(digits) in (10, 11):
        return f'{digits[:4]}-{digits[4:7]}-{digits[7:]}'

    # Landline: only trust if the raw HAD phone structure (avoids treating random
    # 10-digit runs on the page as phones). Validate the STD code.
    if had_structure and 10 <= len(core) <= 11:
        # 2-digit metro STD
        if core[:2] in _VALID_2DIGIT_STD:
            num = core[2:]
            if 6 <= len(num) <= 9:
                half = len(num) // 2
                return f'+91-{core[:2]}-{num[:half]}-{num[half:]}'
        # 3-4 digit STD starting 1-8 (not 0/9)
        for std_len in (3, 4):
            std, num = core[:std_len], core[std_len:]
            if std[0] in '12345678' and 6 <= len(num) <= 8:
                half = len(num) // 2
                return f'+91-{std}-{num[:half]}-{num[half:]}'
    return ''


def _is_plausible(formatted):
    """Reject obvious non-phones (all same digit, sequential, too short)."""
    d = re.sub(r'\D', '', formatted)
    if len(d) < 10:
        return False
    body = d[2:] if d.startswith('91') else d
    if len(set(body)) <= 2:           # 1111111111, 1212121212
        return False
    if body in ('1234567890', '0123456789', '9876543210'[::-1]):
        return False
    return True


def _fetch(url):
    if not _HAS_REQUESTS:
        return ''
    try:
        r = requests.get(url, headers={'User-Agent': UA}, timeout=TIMEOUT,
                         allow_redirects=True)
        if r.status_code == 200 and r.text:
            return r.text
    except requests.RequestException:
        pass
    return ''


def _extract_phones(html):
    """Return list of validated unique Indian phones from HTML text.
    tel: links are trusted (explicit markup). Regex matches must carry phone
    structure (+91 / 0 / parens) to count as landlines."""
    found, seen = [], set()

    # 1) tel: links — explicit, highest trust
    for raw in re.findall(r'tel:([+\d\-\s().]{8,20})', html, re.IGNORECASE):
        fmt = _normalize(raw, had_structure=True)
        if fmt and _is_plausible(fmt) and fmt not in seen:
            seen.add(fmt); found.append(fmt)

    # 2) regex candidates from visible text
    for raw in _PHONE_CANDIDATE.findall(html):
        had_structure = bool(re.search(r'\+?91|\(0?\d{2,4}\)|^0\d', raw.strip()))
        fmt = _normalize(raw, had_structure=had_structure)
        if fmt and _is_plausible(fmt) and fmt not in seen:
            seen.add(fmt); found.append(fmt)
    return found


def find_phone(website):
    """
    Visit a company's own website (home + contact/about pages) and extract its
    published switchboard phone. Returns dict or {} if nothing found.

    Result: {'phone', 'mobile', 'source_url', 'confidence', 'all_found': [...]}
    """
    if not website or not _HAS_REQUESTS:
        return {}
    site = str(website).strip()
    if not site or site.lower() == 'nan':
        return {}
    if '@' in site:                       # not a URL — it's an email
        return {}
    if not site.startswith(('http://', 'https://')):
        site = 'https://' + site
    # Clean to base origin
    parsed = urlparse(site)
    base = f'{parsed.scheme}://{parsed.netloc}'

    all_found, source = [], ''
    for path in CONTACT_PATHS:
        url = urljoin(base + '/', path)
        html = _fetch(url)
        if not html:
            continue
        phones = _extract_phones(html)
        if phones:
            all_found = phones
            source = url
            # Contact pages are higher-confidence; stop once we hit one
            if path and path not in ('about', 'about-us', 'aboutus'):
                break
    if not all_found:
        return {}

    # Split landline (switchboard) vs mobile
    def _is_mobile(p):
        d = re.sub(r'\D', '', p)
        body = d[2:] if d.startswith('91') else d
        return len(body) == 10 and body[0] in '6789'

    landlines = [p for p in all_found if not _is_mobile(p)]
    mobiles   = [p for p in all_found if _is_mobile(p)]

    return {
        'phone':      landlines[0] if landlines else '',
        'mobile':     mobiles[0] if mobiles else '',
        'source_url': source,
        'confidence': 'High',   # straight off the company's own site
        'all_found':  all_found,
        'notes':      f'Switchboard from company website ({source})',
    }


if __name__ == '__main__':
    # Self-test against a few company sites (needs internet)
    for site in ['https://www.batliboi.com', 'https://www.motilaloswal.com']:
        print(f'\n→ {site}')
        r = find_phone(site)
        if r:
            print(f'   phone: {r["phone"]}  mobile: {r["mobile"]}')
            print(f'   source: {r["source_url"]}')
            print(f'   all: {r["all_found"][:5]}')
        else:
            print('   (nothing found / no internet)')
