# Credit Allocation Strategy — Free-Tier Tools

The AIPL team has ~65-70 free credits per month across 4 tools combined:

| Tool | Free credits/month | 1 credit = | Best for |
|---|---:|---|---|
| Lusha | 40 | 1 phone number OR 1 email reveal | Phone numbers (esp. mobile, Indian coverage) |
| Apollo | 10 | 1 contact export (name + email + title + org bundled) | IT-role lookups, bulk-ish exports |
| Signal Hire | 5-10 | 1 full contact unlock (name + email + phone) | Senior decision-makers (CIO/CTO level) |
| Contact Out | 10 | 1 email reveal from LinkedIn | Emails for LinkedIn-active people |

**Total = ~65-70 lookups/month.** This is finite. Wasting credits on the wrong companies = team gets blocked next week.

## Allocation principle

**Spend credits where they ADD value over what Claude already found via web/MCA.** That means:

### DO spend credits on:

1. **Large enterprises where Claude only found the MD/Director** — because at a 5000-employee company, the MD is not the IT decision-maker. The actual CIO/IT Head exists, just isn't public. Use Apollo or Signal Hire to find them.
   - Examples from prior run: ONGC, Motilal Oswal, Hindware, Baroda Global, Aplab, Batliboi, Manugraph

2. **Companies that Claude returned completely blank** — to get *any* contact, even just a Director. Use Lusha (cheap, 40 credits) or Apollo.

3. **High-confidence Director rows where we have a name but no email** — use Contact Out to find the personal email (since MCA only gives the company email).

### DO NOT spend credits on:

1. **Small Pvt Ltds (<50 employees) where Claude already found the MD/Founder.** At that company size, the MD IS the IT decision-maker — calling them is the right play. Spending Apollo credits to find a "CIO" who doesn't exist wastes the credit.

2. **Companies where Claude already returned a verified IT-specific contact with email + phone.** No need to re-verify; trust High-confidence results.

3. **Companies that are clearly dead** (under liquidation, struck off, name not found anywhere) — drop them from outreach entirely.

## Tool-to-company matching (which tool for which type)

Lusha and Contact Out are cheaper per-credit (more credits/month). Apollo and Signal Hire are scarcer — save them for harder/more valuable targets.

| Company profile | Best tool | Why |
|---|---|---|
| Large enterprise, need IT-specific contact | **Apollo** or **Signal Hire** | Best IT-role coverage and verified bundles; worth the scarce credits |
| Found Director name, need their personal email | **Contact Out** | Specialized for LinkedIn-to-email |
| Found Director name, need their phone | **Lusha** | Best Indian mobile coverage |
| Completely blank company, need *any* contact | **Lusha** (try first) → **Apollo** if Lusha fails | Lusha's cheap; Apollo as backup |
| LinkedIn URL known but no contact details | **Contact Out** (for email) + **Lusha** (for phone) | Both work great with a LinkedIn URL as input |
| Senior decision-maker target (CTO/CIO of mid-large co) | **Signal Hire** | Specialized for executive-level bundles |

## Allocation algorithm (use this in `scripts/build_lookup_queue.py`)

Given the master file after Mode A enrichment:

```
1. Score each company by enrichment value:
   - Blank rows (no contact): score = 10  [highest priority — get any contact]
   - Director-only rows at large companies: score = 8  [worth finding actual IT person]
   - Director-only rows at small companies: score = 2  [low ROI — MD is the contact]
   - Already-found IT contact (any size): score = 0  [skip — don't re-enrich]

2. Sort by score descending.

3. Assign top 40 to Lusha queue, next 10 to Apollo, next 10 to Signal Hire, next 10 to Contact Out.

4. Within each tool queue, sort by likely difficulty (use simpler tools on easier-to-find companies and scarcer tools on harder/more valuable ones — see matching table above).

5. Output multi-tab Excel: Lookup_Queue.xlsx with one tab per tool.
```

## Company-size heuristics (since source list rarely has employee count)

Without explicit employee numbers, infer size from the company name pattern:

| Name pattern | Likely size | Treat as |
|---|---|---|
| Government / PSU (ONGC, BHEL, etc.) | 1000+ | Large enterprise |
| `LIMITED` (no Pvt/LLP) and known brand | 500+ | Large/Mid |
| `M/S ... LIMITED` (formal "Messrs" prefix, listed-style) | 100-500 | Mid |
| `... PRIVATE LIMITED` | 10-100 | Small |
| `... LIABILITY PARTNERSHIP` or `LLP` | 5-50 | Small |
| `... SAHAKARI SANSTHA` / `... PATSANTHA` | 5-100 | Cooperative |

This isn't perfect but it's good enough for allocation.

## Sample output (what the team sees)

After running Mode B on the 93-company list, they get `Lookup_Queue.xlsx` with 4 tabs:

**Tab 1 — Lusha (40 credits, top priority):**
| Rank | Company | What to look up | LinkedIn URL (if known) | Notes |
|---|---|---|---|---|
| 1 | M/S DVAULT HOSPITALITY PVT LTD | Director name + phone | (none) | Completely blank — get any contact |
| 2 | M/S REBARCRAFTER PVT LTD | Director name + phone | (none) | Completely blank |
| ... | ... | ... | ... | ... |

**Tab 2 — Apollo (10 credits, IT-specific):**
| Rank | Company | What to look up | Why this tool |
|---|---|---|---|
| 1 | HINDWARE LIMITED | CIO/IT Head email + phone | Large listed; need actual IT person not just MD |
| 2 | ONGC | CIO/IT Head email + phone | PSU, real IT team exists |
| ... | ... | ... | ... |

The team blasts through each tab in their browser tools, exports the results, then runs Mode C to merge back.
