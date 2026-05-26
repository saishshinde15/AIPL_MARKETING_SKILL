# AIPL Marketing — Lead Enrichment Skill

A Claude **Skill** that automates B2B lead enrichment for AIPL's marketing team. Drop a list of Indian companies in, get a Vtiger-ready import file out — with verified IT decision-maker contacts, smart credit allocation across your free-tier paid tools, and zero code visible to the team.

Built for **non-technical users on the Claude.ai $20 Pro plan**. No Terminal, no Python installs, no API keys. Just upload, chat, download.

---

## What this skill does

It runs three modes, all triggered by plain English in the Claude chat:

### Mode A — Enrich a company list

You upload an Excel/CSV of Indian companies. Claude:

1. Web-searches for IT decision-maker contacts (CIO, CTO, IT Head, IT Manager, IT Infra, IT Procurement)
2. Falls back to MCA filings (via Zauba Corp, Tofler) for Director/MD names when IT-specific contacts aren't public
3. Maps everything to the **75-column Vtiger Leads template**
4. Outputs 3 downloadable files: Excel (review), CSV (Vtiger import), Coverage Report (stats)

### Mode B — Prioritized lookup queue for paid tools

The team uses free tiers of 4 B2B databases. Combined budget is ~65-70 credits/month:

| Tool | Free credits/month | Best for |
|---|---:|---|
| **Lusha** | 40 | Phone numbers (Indian mobile coverage) |
| **Apollo** | 10 | IT-role emails (bulk-ish) |
| **Signal Hire** | 5-10 | Senior decision-makers (name + email + phone bundle) |
| **Contact Out** | 10 | Emails from LinkedIn profiles |

Claude ranks every company in your master file by enrichment value, then outputs a **4-tab Excel** telling the team exactly which companies to look up in which tool — no wasted credits.

### Mode C — Merge tool exports back

After the team manually unlocks contacts in their browser tools, they upload the exports. Claude auto-detects which tool each file came from, merges into the master file without overwriting verified data, and re-emits the final Vtiger-ready CSV.

---

## Installation

### Prerequisites
- A **Claude.ai $20 Pro** subscription (or higher tier)
- The file `aipl-lead-enrichment.skill` from this repo

### Steps

1. **Download the skill file:**
   - From this repo: click `aipl-lead-enrichment.skill` → click "View raw" or "Download"
   - Save it anywhere on your computer

2. **Open Claude.ai** in your browser → log in

3. **Go to Settings:**
   - Click your profile icon (top-right) → **Settings**
   - In the left sidebar, click **Capabilities** → **Skills**

4. **Upload the skill:**
   - Click **"Upload skill"** (or drag-and-drop the file)
   - Select `aipl-lead-enrichment.skill`
   - Confirm install

5. **Done.** Claude will show ✅ "aipl-lead-enrichment installed". The skill is now active in every chat — Claude will auto-detect when to use it.

---

## How to use it

### Weekly workflow

**Monday — enrich the week's new company list (Mode A)**

1. Open Claude.ai → start a new chat
2. Upload your company list (Excel or CSV — columns: `EnterpriseName`, `Address`, `State`, `District`, `Pincode`)
3. Type: **"run AIPL enrichment on this"**
4. Wait 10-20 minutes while Claude searches the web for each company
5. Download the 3 generated files:
   - `Hygienic_Leads.xlsx` — review in Excel
   - `Hygienic_Leads.csv` — for Vtiger import
   - `Hygienic_Leads_Coverage_Report.txt` — stats + list of blanks

**Tuesday — generate the lookup queue (Mode B)**

1. In the same chat (or new chat with the master file uploaded), type: **"generate the paid-tools lookup queue"**
2. Download `Lookup_Queue.xlsx` — 4 tabs (one per tool), with rows sorted by priority

**Tuesday-Wednesday — manual tool lookups**

Open each tab and use the browser extensions:
- Lusha tab → look up those 40 companies in Lusha, export results to CSV
- Apollo tab → look up those 10, export to CSV
- Signal Hire tab → look up those 10, export to CSV
- Contact Out tab → look up those ~10, export to CSV

**Thursday — merge exports back (Mode C)**

1. Open a new chat in Claude.ai
2. Upload all 4 tool export CSVs + the master file from Monday
3. Type: **"merge these tool exports into the master file"**
4. Claude auto-detects which tool each file came from, merges without overwriting verified data
5. Download `Hygienic_Leads_Updated.csv`

**Friday — Vtiger import**

1. Log in to Vtiger CRM
2. Go to Leads → Import
3. Upload `Hygienic_Leads_Updated.csv`
4. Confirm column mapping → import

That's it. Total team time per week: ~1 hour of clicking in browser tools + ~10 min of Claude chat.

---

## File structure

```
AIPL_MARKETING_SKILL/
├── aipl-lead-enrichment.skill        # Packaged skill file (upload this to Claude.ai)
├── aipl-lead-enrichment/             # Unpacked skill source (for editing/review)
│   ├── SKILL.md                      # Main playbook (what Claude reads first)
│   ├── references/                   # Reference docs (loaded as needed)
│   │   ├── vtiger-schema.md          # 75-column Vtiger format + defaults
│   │   ├── enrichment-sources.md     # LinkedIn, Zauba, MCA search patterns
│   │   ├── credit-allocation.md      # How to spend 65 free credits smartly
│   │   └── target-roles.md           # The 4 IT personas + designation mapping
│   ├── scripts/                      # Python helpers (run in Claude's analysis tool)
│   │   ├── build_vtiger_file.py      # Mode A — generate Vtiger XLSX + CSV
│   │   ├── build_lookup_queue.py     # Mode B — prioritize 65 credits across 4 tools
│   │   └── merge_tool_exports.py     # Mode C — merge Lusha/Apollo/etc. exports
│   └── assets/
│       └── vtiger_template_headers.tsv  # Reference column order
└── README.md                          # This file
```

---

## What the skill enforces (guardrails)

These rules are baked into the skill so the data quality stays clean:

1. **Never fabricates data.** If a name/email/phone isn't found, the field stays blank. The team will cold-call the switchboard for blanks.
2. **Always cites source URLs.** Every populated row has the source URL (LinkedIn, Zauba, company site) in the `Additional Details` column, so the team can verify before calling.
3. **Confidence tagging.** Every enriched row is marked High / Medium / Low confidence so the team knows what to trust.
4. **Role flagging.** When the only contact found is a Director/MD (not IT-specific), the row is flagged: `"ROLE FLAG: Not IT-specific — use as gatekeeper to reach IT decision-maker"`.
5. **Word-boundary designation matching.** Avoids the classic bug where `"Director"` gets misclassified as `"CTO"` due to substring match.
6. **Vtiger defaults.** Every row gets the same standing defaults: Lead Source = `Master DB`, Lead Status = `Prospect`, Currency = `INR`, Country = `India`, etc. Team doesn't have to set these manually.

---

## Realistic coverage expectations

| Setup | Realistic coverage |
|---|---:|
| Free tier (this skill + 4 free-tier tools) | **80-85%** |
| + Apollo paid plan ($49/mo) | 88-92% |
| + Lusha paid ($79/mo) + Apollo | 92-95% |
| 100% | Impossible (very new Pvt Ltds simply don't exist on any public source) |

The 15-20% gap = micro Pvt Ltds with no web presence + cooperative societies + sole proprietorships. These require either MCA21 manual lookup at mca.gov.in or cold-calling switchboards. No automation reaches them.

---

## AIPL's 4 target IT decision-maker roles

The skill is built around these personas (in priority order):

1. **VP IT / CISO / CTO** — Strategic budget owners (large enterprises only)
2. **IT Manager / IT Head** — Operational lead (most common at any mid+ size company)
3. **IT Infra / Sr. IT Infra** — Technical evaluator (mid-large companies with infra teams)
4. **IT Procurement / Purchase** — Commercial gatekeeper (formalized procurement at larger cos)

Designation mapping logic uses **word-boundary matching** (not substring) — see `references/target-roles.md` for the full rules.

---

## Updating the skill

When you want to change the workflow / add a new mode / change defaults:

1. Edit the files in `aipl-lead-enrichment/` (e.g., `SKILL.md`, references, scripts)
2. Re-package the skill — easiest way is via Claude Code:
   ```bash
   # In a Claude Code session
   "package the aipl-lead-enrichment skill"
   ```
   Or manually using the skill-creator's `package_skill.py` from anthropic-skills.
3. Re-upload the new `.skill` file in Claude.ai → Settings → Skills (replaces the old version)

---

## License

Internal use at AIPL. Not for public redistribution.

---

## Credits

Built for AIPL Marketing Team, May 2026.
