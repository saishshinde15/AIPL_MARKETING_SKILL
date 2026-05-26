# Enrichment Sources — Where to Look and How to Search

This is the playbook for finding IT decision-maker contacts at Indian companies. Use web search (built into Claude) to query these sources. Stop at the first useful hit per company.

## Source priority (in order)

For each company, try these in sequence. Move to the next only if the previous didn't yield a name.

### 1) LinkedIn (best for IT-specific roles at mid-large companies)

**Search query template:**
```
"<CompanyName>" (CIO OR CTO OR "IT Head" OR "IT Manager") site:linkedin.com/in
```

LinkedIn blocks scraping but Google indexes the public search snippets — these usually show `Name — Title at Company` in the snippet. That's enough to populate First/Last/Designation. Don't try to fetch the LinkedIn page itself (it'll redirect to login).

**Variations to try:**
- `"<CompanyName>" "VP IT" OR "Vice President Information Technology" linkedin`
- `"<CompanyName>" "Head of Technology" OR "Head - IT" linkedin`
- `"<CompanyName>" CIO India linkedin`

### 2) Company's own website (best for medium companies that publish leadership)

**Search query template:**
```
"<CompanyName>" leadership team OR management OR "about us"
```

Then WebFetch the company's "About Us", "Leadership", or "Management" page if a URL appears in results. Look for the IT/Technology section. Many Indian listed companies (BSE/NSE) publish KMP (Key Managerial Personnel) lists — those include the CIO/CTO.

### 3) MCA filings via Zauba Corp / Tofler (best for any registered Indian company)

**Every Indian Pvt Ltd, LLP, and Limited company is required by law to file with the Ministry of Corporate Affairs (MCA).** This data is aggregated and indexed by free third-party portals.

**Search query template:**
```
"<CompanyName>" site:zaubacorp.com
```
or
```
"<CompanyName>" director CIN
```

Then WebFetch the Zauba page if it appears. The page typically shows:
- **CIN** (Corporate Identification Number) — useful for verification
- **Registered email** — official company email on file with MCA
- **Directors list** — full names, DIN numbers, dates appointed

**What MCA gives you:** Director/MD name + registered email. **What it does not give you:** the IT Manager or CIO (MCA only tracks legal directors, not departmental heads). For small Pvt Ltds (under 100 employees), the MD usually IS the IT decision-maker — this is fine.

**Alternative MCA portals to try if Zauba is empty:**
- `<CompanyName> tofler.in`
- `<CompanyName> instafinancials`
- `<CompanyName> indiafilings`
- `<CompanyName> quickcompany`

### 4) Business directories (last resort — gets switchboard phone only)

**Search query template:**
```
"<CompanyName>" Mumbai phone contact
```

Sites that often surface:
- IndiaMart (`indiamart.com`)
- JustDial (`justdial.com`)
- Sulekha (`sulekha.com`)
- Grotal (`grotal.com`)

These rarely have a contact person's name, but they often have the company switchboard number and website. Useful for the team's cold-call list.

### 5) BSE/NSE filings (only for listed companies)

If the company is on the stock exchange (CIN starting with `L`), the BSE/NSE site shows annual reports listing all KMP including the CIO/CTO. Search:
```
"<CompanyName>" "annual report" KMP CIO
```

## How to handle each finding

When you get a hit, extract:

| Want | How to get it |
|---|---|
| First Name + Last Name | Split full name on first space; everything before = First, rest = Last |
| Salutation | Infer from first name (Indian common names): `Mr.` default; `Ms.` for clearly female names like Priya, Neha, Pooja, Anita, Smita, Asha, Sneha, Meera, Sunita, Geeta, Seema, Kavita, Rekha, Shilpa, Swati, Divya, Jyoti, Suman |
| Designation | The actual title from the source (don't pre-map yet — that happens at output stage per `vtiger-schema.md`) |
| Email | Only if it's literally printed on the source page. **Don't pattern-guess like `firstname.lastname@company.com`** — that creates bad data. |
| Office Phone | Company switchboard from website or directory |
| Mobile | Only if PUBLICLY listed; never guess |
| Website | Company website URL |
| Source URL | The exact URL where you found the contact (always record this) |
| Confidence | High = directly verified on company site or LinkedIn current job; Medium = MCA filing or LinkedIn snippet; Low = old article, inferred, or partial match |

## Search budget per company

Be efficient. Aim for **2-3 searches per company max** on initial enrichment. If nothing surfaces after that, move on — extra searches rarely help for small Pvt Ltds with no public footprint.

For a list of 90+ companies, that's 180-270 searches total. Spread across web search and WebFetch, this is doable in one chat session but takes 10-20 minutes of execution. Keep the user updated on progress.

## When you can't find anything

Some companies simply have zero public web presence. Common reasons:
- **Very recently incorporated** (2023-2025) — not yet indexed by aggregators
- **Cooperative society** (Sahakari Sanstha) — not under MCA, registered under state Cooperative Registrar
- **Proprietorship** — no formal MCA registration
- **Address mismatch** — registered in a different city than the source list shows
- **Name variant or typo** — "PR IVA TE LIMITED" vs "PRIVATE LIMITED"

For these, leave the contact fields blank but flag in `Additional Details`:
```
Notes: No public web/MCA presence under this exact name. Likely a very new entity or name variant. Recommend manual MCA21 lookup at mca.gov.in.
```

## Tool Export Formats (Mode C — merging back)

When the user uploads exports from the 4 paid tools, auto-detect by these column signatures:

| Tool | Typical columns in export | Detection signal |
|---|---|---|
| **Lusha** | `First Name`, `Last Name`, `Title`, `Company`, `Email`, `Phone`, `LinkedIn Url` | Has both `Phone` and `LinkedIn Url` columns; "Lusha" often in filename |
| **Apollo** | `First Name`, `Last Name`, `Title`, `Email`, `Mobile Phone`, `Corporate Phone`, `Organization Name` | Has `Corporate Phone` + `Organization Name`; filename often `apollo-contacts-export-*` |
| **Signal Hire** | `Full Name`, `Position`, `Company`, `Email 1`, `Email 2`, `Phone 1`, `Phone 2` | Has multiple Email/Phone columns; "SignalHire" in filename |
| **Contact Out** | `Name`, `Title`, `Company`, `Email`, `Personal Email`, `LinkedIn URL` | Has `Personal Email` column; "ContactOut" in filename |

Mapping rules for merge:
- Match rows by Company name (fuzzy — strip "M/S", "Limited", "Pvt Ltd", "Private Limited", and compare lowercased trimmed versions).
- If company matches, take the tool's First/Last/Title/Email/Phone — but **don't overwrite** existing non-empty fields in the master.
- Always append the tool name to `Additional Details`: `Source: Lusha (manual unlock)` etc.
- Update Confidence to `High` since these tools verify their data.

## Quick reference — what works for which company size

| Company size | Best source | Expected hit rate |
|---|---|---|
| Large listed (PSU, BSE-listed, 1000+ emp) | LinkedIn + company site + BSE filings | 70-90% IT-specific |
| Mid-size Limited (100-1000 emp) | LinkedIn + Zauba | 40-60% IT-specific; 80%+ MD/Director |
| Small Pvt Ltd (10-100 emp) | Zauba (Director only) | 70%+ Director name |
| Micro Pvt Ltd (<10 emp, < 2 years old) | Often nothing | 20-40%; usually blank |
| LLP | Tofler (Designated Partners) | 50-70% |
| Sahakari Sanstha | Maharashtra Coop Registrar (manual, not online) | <10% |
| Proprietorship | Business directories only | Switchboard only |
