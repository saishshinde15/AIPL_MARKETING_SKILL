"""
google_places_phone.py
======================
Look up a company's business phone via the Google Places API.

Google Maps lists most established Indian businesses with their switchboard
number. The Places API returns it legitimately (official API, no scraping).
Google grants a recurring free monthly credit (~$200) which covers thousands
of lookups — far more than AIPL's volume.

CONFIG:
    Set environment variable GOOGLE_PLACES_KEY before invoking the skill.
    Get a free key:
      1. https://console.cloud.google.com/  → create/select a project
      2. Enable "Places API"
      3. Credentials → Create API key
      4. export GOOGLE_PLACES_KEY=AIza...

    Without a key, this module is a graceful no-op — the skill keeps working,
    you just lose the bonus phone coverage.

WHAT IT RETURNS: the business switchboard / office number (not the IT Head's
personal mobile). Pair it with the skill's "call and ask for IT Head" scripts.

USAGE:
    from google_places_phone import lookup, available
    if available():
        r = lookup("Batliboi Limited", city="Mumbai")
        # → {'phone': '+91-22-2493-4000', 'name': 'Batliboi Ltd',
        #    'address': '...', 'source_url': '...', 'confidence': 'High'}
"""
import os
import re
import json

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

ENV_KEY = "GOOGLE_PLACES_KEY"
FIND_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
TIMEOUT = 12


def available():
    """True if we can actually call the API (deps + key present)."""
    return _HAS_REQUESTS and bool(os.environ.get(ENV_KEY))


def _normalize_phone(raw):
    """Format a Google-returned Indian phone to +91-XX-XXXX-XXXX style."""
    if not raw:
        return ''
    digits = re.sub(r'\D', '', raw)
    if digits.startswith('91') and len(digits) == 12:
        rest = digits[2:]
    elif len(digits) == 10:
        rest = digits
    elif digits.startswith('0') and len(digits) == 11:
        rest = digits[1:]
    else:
        return raw.strip()  # unknown shape — return Google's formatting as-is
    # Mobile vs landline
    if rest[0] in '6789' and len(rest) == 10:
        return f'+91-{rest[:5]}-{rest[5:]}'
    # Landline: split metro 2-digit vs 3-4 digit STD
    for std_len in (2, 3, 4):
        std, num = rest[:std_len], rest[std_len:]
        if 6 <= len(num) <= 8:
            half = len(num) // 2
            return f'+91-{std}-{num[:half]}-{num[half:]}'
    return f'+91-{rest}'


def lookup(company_name, city=''):
    """
    Look up a company's business phone via Google Places.
    Returns dict or {} (no key / not found / error).

    Result: {'phone','name','address','source_url','confidence'}
    """
    if not available() or not company_name:
        return {}
    key = os.environ[ENV_KEY]
    query = company_name.strip()
    if city:
        query = f'{query} {city}'

    try:
        # 1) Find Place → place_id
        fr = requests.get(FIND_URL, params={
            'input': query, 'inputtype': 'textquery',
            'fields': 'place_id,name,formatted_address',
            'region': 'in', 'key': key,
        }, timeout=TIMEOUT)
        if fr.status_code != 200:
            if fr.status_code in (401, 403):
                os.environ.pop(ENV_KEY, None)  # bad key — disable for session
            return {}
        fdata = fr.json()
        candidates = fdata.get('candidates', [])
        if not candidates:
            return {}
        place = candidates[0]
        place_id = place.get('place_id')
        if not place_id:
            return {}

        # 2) Place Details → phone
        dr = requests.get(DETAILS_URL, params={
            'place_id': place_id,
            'fields': 'name,formatted_phone_number,international_phone_number,formatted_address,website',
            'region': 'in', 'key': key,
        }, timeout=TIMEOUT)
        if dr.status_code != 200:
            return {}
        d = dr.json().get('result', {})
        phone_raw = d.get('international_phone_number') or d.get('formatted_phone_number') or ''
        if not phone_raw:
            return {}

        return {
            'phone':      _normalize_phone(phone_raw),
            'name':       d.get('name', place.get('name', '')),
            'address':    d.get('formatted_address', ''),
            'website':    d.get('website', ''),
            'source_url': f'https://www.google.com/maps/place/?q=place_id:{place_id}',
            'confidence': 'High',  # Google-verified business listing
            'notes':      'Switchboard via Google Places API',
        }
    except (requests.RequestException, ValueError, KeyError):
        return {}


if __name__ == '__main__':
    print(f"Google Places lookup available: {available()}")
    if available():
        for name, city in [("Batliboi Limited", "Mumbai"),
                           ("Bajaj Finance Ltd", "Pune")]:
            r = lookup(name, city)
            print(f"\n{name}:")
            print(json.dumps(r, indent=2) if r else "  (not found)")
    else:
        print(f"\nTo enable: get a free key at https://console.cloud.google.com/")
        print(f"  1. Enable 'Places API'  2. Create API key")
        print(f"  3. export {ENV_KEY}=AIza...")
        print(f"\nGoogle grants ~$200/month free credit = thousands of lookups.")
