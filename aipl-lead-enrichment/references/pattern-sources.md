# Pattern-finding sources — where to prove a company's email format (free, ethical)

The goal: find ONE real, **published**, person-style example email at a company's
mail domain (a name in the local-part — NOT `info@`/`grievance@`). From that one
real address you read off the **format**, then derive the decision-maker's email
(`derive_emails.py`). Only patterns proven by a real observed address — never a guess.

## Source ranking (best first)

1. **NHB "List of Nodal Officers / Point of Contacts of HFCs" PDF** ⭐⭐⭐
   - The single richest source for Housing-Finance & many NBFC contacts.
   - Prints, per company: officer NAME + real EMAIL + phone. One row = a proven pattern.
   - Find it: search `NHB nodal officers HFC pdf` / browse nhb.org.in. Multiple
     editions exist (e.g. Aug-2024, Sep-2025, Mar-2026) — the newer ones have
     cleaner person-style addresses; cross-check across editions.
   - Extract from the PDF TEXT (not a screenshot) to avoid column-wrap errors
     that split a domain across lines.

2. **BSE / NSE filings, IPO prospectuses, annual reports** ⭐⭐⭐ (listed cos)
   - Company Secretary / Compliance Officer / KMP emails are **legally required to
     be published** → real, named, verifiable. Gold for listed/SEBI-registered cos.
   - Search `"<Company>" company secretary email BSE` or the investor-relations page.

3. **Company's own Team / Leadership / Contact / Grievance-officer page** ⭐⭐
   - Many mid/small firms name a person + email here. Always check first.

4. **Press releases, award write-ups, conference/speaker bios** ⭐
   - Often a named media or exec contact with a real address.

5. **Public-PDF email signatures** (tenders, board notices, circulars) ⭐
   - A real signature address proves the format.

## ⚠ Mail domain ≠ website domain (capture the override)
The address you'll send to often lives on a DIFFERENT domain than the website.
Real examples seen:
- bajajhousingfinance.in (site) → **bajajhousing.co.in** (mail)
- saharahousingfina.com → **sahara.in**
- an Adani housing entity → **tyger.in** (rebrand)
- centrum site `chfl.co.in` → **centrum.co.in**
- capitalindiahomeloans.com → **capitalindia.com** (parent)
- truhomefinance.com → **truhomefinance.in**
- GIC Housing site `gichfindia.com` → **gichf.com**

When the proven example is on a sibling domain, record it as a `mail_overrides`
entry (`{company-keyword: real_mail_domain}`) so derivation uses the right domain.

## Classifying the pattern (from one real address `jane.doe@acme.com`)
| Local-part of the example | pattern |
|---|---|
| `jane.doe` | `first.last` |
| `janedoe` | `firstlast` |
| `jdoe` | `flast` |
| `jane` | `first` |
| `jane_doe` | `first_last` |
| `doe.jane` | `last.first` |
| `jane.d` | `first.l` |
| `j.doe` | `f.last` |

Odd local-parts that don't map cleanly (e.g. `finitials.last`, surname-first-no-
separator) → **leave the pattern unproven** rather than force a derivation.

## Hard rules
- Only a REAL published person-style address proves a pattern. A role inbox
  (`grievance@`/`info@`/`gro@`) confirms the domain but **NOT** the format.
- Broker-asserted patterns (RocketReach/ZoomInfo "this company uses first.last")
  with no visible real address = **not proof**. Don't seed those.
- No proof → leave the email blank. A named lead with a blank email beats a wrong one.
