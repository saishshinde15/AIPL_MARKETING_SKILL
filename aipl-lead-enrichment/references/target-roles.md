# AIPL's 4 Target IT Decision-Maker Roles

AIPL sells IT and networking infrastructure to Indian enterprises. They've defined exactly 4 personas to target. Every enriched contact should ideally map to one of these.

## The 4 target roles (priority order for outreach)

### 1. VP IT / CISO / CTO  (highest seniority)

**Who they are:** C-suite or VP-level IT executives. They own the IT strategy and budget for the whole company.

**Title variants to recognize:**
- Chief Information Officer (CIO)
- Chief Technology Officer (CTO)
- Chief Information Security Officer (CISO)
- Chief Digital Officer (CDO)
- VP IT / VP Technology / VP Information Technology
- Senior VP IT / Sr. VP & CIO
- Vice President Information Systems
- Group CIO / Group CTO (for conglomerates)
- Executive Director - IT

**Where they exist:** Large enterprises (1000+ employees), listed companies, MNCs, PSUs. Almost never at small Pvt Ltds.

**Why AIPL wants them:** Final budget authority. If you sell to the CIO, the deal closes faster.

### 2. IT Manager / IT Head  (operational lead)

**Who they are:** The day-to-day owner of IT operations. Reports to the CIO at large cos, reports directly to MD at smaller ones.

**Title variants:**
- IT Manager / Manager - IT
- IT Head / Head - IT / Head of IT
- Information Technology Manager
- IT Operations Manager
- Manager, Information Technology
- Sr. Manager IT
- IT Lead

**Where they exist:** Almost every company with 50+ employees has someone with this title (or doubles up with another role).

**Why AIPL wants them:** The user/evaluator of the product. They influence the purchase decision and run the day-to-day relationship with the vendor.

### 3. IT Infra / Sr. IT Infra  (technical specialist)

**Who they are:** Owns networking, servers, infrastructure — the technical evaluator for AIPL's products specifically.

**Title variants:**
- IT Infrastructure Manager / Head
- Sr. IT Infrastructure Engineer
- Network Manager / Network Head
- Infrastructure Lead
- Systems Manager
- Datacenter Manager

**Where they exist:** Mid-large companies with dedicated infra teams (100+ employees, typically tech-heavy or data-heavy businesses like BFSI, manufacturing, healthcare).

**Why AIPL wants them:** Most technically credible buyer for networking products. They evaluate solutions on technical merits.

### 4. IT Procurement / Purchase  (commercial gatekeeper)

**Who they are:** Owns the vendor onboarding, PO process, contract negotiation for IT spend.

**Title variants:**
- IT Procurement Manager / Head
- Purchase Head - IT
- Strategic Sourcing - IT
- Vendor Management Lead
- Indirect Procurement (IT category)

**Where they exist:** Larger companies (500+ employees) with formalized procurement processes. Small Pvt Ltds usually have the MD handle this directly.

**Why AIPL wants them:** Final commercial signoff. Often the last gate before a deal closes.

## Designation mapping (use word-boundary matching!)

When the found title has any of these EXACT WORDS (not substrings — be careful!), map accordingly:

```
"CIO" | "CTO" | "CISO" | "Chief Information Officer" | "Chief Technology Officer"
| "VP IT" | "VP Technology" | "VP Information" | "Vice President IT" | "Vice President Technology"
                                                                 → VP IT / CISO / CTO

"IT Infra" | "Infrastructure Head" | "Infrastructure Manager" | "Infrastructure Lead"
                                                                 → IT Infra / Sr. IT Infra

"IT Procurement" | "IT Purchase" | "IT Purchasing" | "Procurement Head" | "Purchase Head"
                                                                 → IT Procurement / Purchase

"IT Head" | "Head of IT" | "Head - IT" | "Head-IT" | "IT Manager" | "Manager IT" | "Manager-IT"
| "Head of Technology" | "Head of Digital" | "IT Lead" | "Sr VP & CIO"
                                                                 → IT Manager / IT Head

Anything else (Director, MD, Founder, CEO, Owner, etc.)
                                                                 → Keep the actual title verbatim
                                                                   AND flag in Additional Details as
                                                                   "ROLE FLAG: Not IT-specific — gatekeeper"

No designation found at all
                                                                 → Default to "IT Manager / IT Head"
                                                                   (most common IT entry point)
```

## ⚠️ Common substring pitfalls (DO NOT match on)

The classic bug: `"director".lower()` contains the substring `"cto"`. Word-boundary matching prevents this.

| Bad match | Why it's wrong |
|---|---|
| `"Director"` → mapped to CTO | "Director" contains chars c,t,o consecutively |
| `"Constructor"` → mapped to CTO | Same issue |
| `"Inspector"` → mapped to CIO | Same issue with "cio" |
| `"Vice President Sales"` → mapped to VP IT | "Vice President" alone isn't IT |
| `"Director of Procurement"` → mapped to IT Procurement | Generic procurement isn't IT procurement |

When in doubt: if the title doesn't explicitly mention IT / Technology / Information, **keep the actual title verbatim** and flag as gatekeeper.

## The reality at small companies

For ~50% of the list (small Pvt Ltds), there is no separate IT person at all. The owner/MD/Founder doubles as the IT decision-maker. In those cases:

- **Don't fake it** by labeling them "IT Manager / IT Head"
- **Do flag clearly** in Additional Details: `ROLE FLAG: Not IT-specific — use as gatekeeper to reach IT decision-maker`
- The team's tele-callers will use the MD's name to introduce themselves, then ask "who handles your IT/networking?" once on the call

This is the standard B2B playbook for SME outreach in India. The flag tells the caller "don't pitch the product to this person, ask them to transfer you".
