# Free Phone-Number Research Waterfall (no API, no card)

Phones matter as much as emails to AIPL. The smart way to get them for free is
**Claude's own web research** reading public surfaces — NOT paid maps APIs
(Google/HERE both need a credit card) and NOT bulk-scraping aggregators.

This works in the Claude.ai desktop app because Claude does the searching with
its own web tools — it does not depend on the code sandbox having internet.

**Golden rule:** never fabricate. If no phone appears on any public surface,
leave it blank. Always cite where the number came from in `Additional Details`.

---

## The waterfall — try in this order, stop at first solid hit

### 1. Google "business card" via a normal web search  ⭐ highest yield
Search: `"<Company Name>" <city>` or `"<Company Name>" contact number`

When a business has a Google Maps presence, Google shows a **business card /
knowledge panel** right in the search results — with the phone number visible.
**Read it straight from the results.** This is just reading a public search
result (not the paid Places API, not scraping Maps). Catches most established
companies, including ones with **no website**.

Cite as: `Source: Google business listing`.

### 2. The company's own website — Contact / About / Footer
Search: `<Company Name> official website contact`
Open the Contact/About page (or just the homepage footer). The switchboard is
almost always published there. `website_phone_finder.py` automates this when
the sandbox has internet; otherwise read it yourself.

Cite as: `Source: <the contact page URL>`.

### 3. For LISTED / public companies — BSE / NSE / annual report
Public Ltd companies publish their **registered-office phone** on:
- **BSE company page**: search `<Company> bseindia.com` → registered office + phone
- **NSE company page**: search `<Company> nseindia.com`
- **Annual report / investor-relations page**: registered office contact block
- **Tofler / Zauba Corp**: sometimes list the registered phone alongside the CIN

Reliable for the public-Ltd / mid-large segment.

### 4. Public social / marketplace profiles
Most Indian SMEs without a website still have a public profile somewhere with a
phone:
- **LinkedIn company page** — often lists a phone under "About"
- **Facebook business page** — "Contact" section
- **Instagram business profile** — "Call" button reveals the number
- **IndiaMART / TradeIndia / ExportersIndia seller profile** — if the number is
  shown in the public profile or the search-result snippet, it's usable. (Do NOT
  build an automated bot that bulk-hits these sites — but reading a number that's
  publicly displayed is fine.)

Cite the specific profile URL.

### 5. Sector / chamber-of-commerce directories
Industry bodies publish member directories with contact numbers — free + public:
- **CII, FICCI, ASSOCHAM, NASSCOM** member directories
- Regional chambers (Bombay Chamber, MCCIA Pune, etc.)
- Sector associations (e.g., textile/pharma/logistics councils)
Especially useful when the source file is sector-segmented (e.g. "NBFC",
"Securities", "HFC").

### 6. MCA registered-office phone (last resort)
Zauba Corp / Tofler occasionally surface the registered phone from MCA filings.
Lower hit-rate, but free.

---

## What this realistically gets you

| Segment | Likely free phone source | Hit rate |
|---|---|---|
| Established mid-large / listed | Google card + BSE/NSE + website | High (70-85%) |
| SME with a website | Website contact page + Google card | Medium-high (60-70%) |
| SME with no website but a shop/office | Google business card | Medium (40-55%) |
| Tiny new Pvt Ltd, no web/maps presence | — (genuinely none) | ~0% |

Blended realistic free phone coverage: **~45-60%** — no card, no API, no cost.

---

## What these phones ARE (set the team's expectation)

These are **office switchboards / main business lines**, not the IT decision-
maker's personal mobile. That's fine — pair them with the "call and ask for the
IT Head" scripts. The only thing that reliably delivers a decision-maker's
**direct mobile** is a paid India tool (EazyReach — DIN-based, INR pricing);
recommend that to AIPL only if switchboard coverage isn't enough.

---

## What we explicitly do NOT do

- ❌ Pay for Google Places / HERE Maps (both require a credit card)
- ❌ Build automated bots that bulk-scrape JustDial / IndiaMART servers
- ❌ Fabricate a number when none is published
- ❌ Use "GST-to-phone" gray-market APIs (DPDP-Act risk)
