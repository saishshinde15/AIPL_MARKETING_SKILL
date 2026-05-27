# AIPL Lead Enrichment — Weekly Runbook

**For:** AIPL Marketing Team
**How to use this doc:** Print it. Keep it next to your laptop. Follow the steps in order.

---

## What you need (one-time setup)

- ✅ Claude.ai Pro subscription ($20/month) — log in at https://claude.ai
- ✅ The skill installed — go to Settings → Capabilities → Skills → confirm `aipl-lead-enrichment` is active
- ✅ Browser logins to: Lusha, Apollo, Signal Hire, Contact Out (free tiers)
- ✅ Vtiger CRM login

If any of these are missing, ping the contractor before starting.

---

## The weekly workflow (90 minutes total, spread over 2 days)

### MONDAY morning — Run enrichment (15 minutes of your time, Claude does the rest)

1. Open https://claude.ai → start a new chat
2. Click the paperclip → upload the week's new company list (e.g., `Limited Medium Enterprise.xlsx`)
3. Type: **`run AIPL pipeline`**
4. Wait. Claude will research each company (~10-30 min depending on list size).
5. When done, Claude will show a summary like:
   > ✅ 73/93 contacts found (78%). Files ready to download.
6. **Download all 4 files:**
   - `Hygienic_Leads.xlsx` — for review
   - `Hygienic_Leads.csv` — for Vtiger import (don't open in Excel before importing!)
   - `Hygienic_Leads_Coverage_Report.txt` — read this
   - `Hygienic_Leads_Mode_B_Action_Sheet.md` — **your todo for Tuesday**

---

### MONDAY afternoon — Quick review (10 minutes)

1. Open `Hygienic_Leads_Coverage_Report.txt` in any text editor (TextEdit, Notepad, VS Code).
2. Scan the **SUMMARY** at the top. You should see something like:
   ```
   ✓ Ready to call directly:       1   ← these are gold, call today
   ↻ Call gatekeeper for IT Head:  25  ← call switchboard, ask for IT person
   ☎ Cold-call switchboard:        4
   📋 MCA portal lookup needed:    16  ← team manual work
   💳 Use Lusha credit:            33
   💳 Use Apollo credit:            8
   ```
3. **Today's quick wins:** Call any rows in the "READY TO CALL DIRECTLY" section. They have full info.

---

### TUESDAY — Work the Action Sheet (60 minutes)

Open `Hygienic_Leads_Mode_B_Action_Sheet.md` in any markdown viewer (or text editor).

It looks like:
```
## Lusha (33/40 credits)

- [ ] 1. Rubin Builders And Infra Limited (Mumbai)
       Current contact: (no name yet) — IT Manager / IT Head
       LinkedIn: https://linkedin.com/...
       What to get: switchboard phone

- [ ] 2. SKY INDUSTRIES LIMITED (Mumbai)
       ...
```

**For each section (Lusha, Apollo, Signal Hire, Contact Out):**

1. Open the tool's browser extension (Lusha icon, Apollo icon, etc.)
2. Look up each company in order
3. **Click the checkbox in the markdown** as you finish each one (so you don't lose your place)
4. After all unlocks in that tool: click the tool's **"Export to CSV"** button. Save somewhere obvious (Desktop or Downloads).

**Time budget:**
- Lusha (40 lookups): ~25 min
- Apollo (10 lookups): ~10 min
- Signal Hire (10 lookups): ~10 min
- Contact Out (10 lookups): ~10 min
- **Total: ~55-60 min of clicking**

**Important rule:** Only spend credits on the companies the Action Sheet lists. Don't randomly look up other companies — wastes your monthly free credits.

---

### THURSDAY — Merge exports back (15 minutes)

1. Open a NEW Claude.ai chat
2. Upload all 4 export CSVs from Tuesday's tool unlocks (drag-and-drop all 4 at once)
3. ALSO upload `Hygienic_Leads.xlsx` from Monday (Claude needs the master to merge into)
4. Type: **`merge these into the master file`**
5. Claude will:
   - Auto-detect which CSV came from which tool
   - Match each export contact to the right company
   - Backfill blanks WITHOUT overwriting verified data
   - Re-emit a final updated CSV
6. Download `Hygienic_Leads_Updated.csv`

---

### FRIDAY — Vtiger import (15 minutes)

1. Log into Vtiger CRM
2. Go to **Leads** → **Import**
3. Upload `Hygienic_Leads_Updated.csv`
4. Confirm column mapping (Vtiger should auto-match all 75 columns since the skill uses the standard schema)
5. Click **Import**
6. Vtiger will show "N leads imported successfully"

**Done. Total time this week: ~90 minutes for ~95% lead coverage.**

---

## Common things you'll see

### "20 still blank — 16 need MCA portal lookup"

These are very new Pvt Ltds (incorporated 2024-2025) that aren't in Zauba/Tofler yet. The Coverage Report tells you to:
- Go to https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do
- Click "Find CIN/LLPIN"
- Type the company name
- Solve the CAPTCHA
- Pull Director details

Estimate: ~5 min per company. Do these only if you have time — they're the lowest-value 16 cos in the list usually.

### "ROLE FLAG: Not IT-specific — use as gatekeeper"

The skill found a Director or MD, NOT an IT-specific person. **What to do:** call the Director, politely ask "may I please speak to your IT Head or IT Manager?" — usually they'll connect you or give you a name + extension.

### "Designation: Gatekeeper - Director"

Same as above — this is a Director/MD/etc., not the IT decision-maker. Use them as a stepping stone.

### "Confidence: Low"

The data was found but not strongly verified (e.g., from a partial LinkedIn snippet or similar-name match). **What to do:** verify by visiting the LinkedIn URL in the Additional Details column BEFORE calling.

---

## Words to say in Claude

You don't have to be precise. These all work:

- `run AIPL pipeline` ← preferred
- `run AIPL enrichment on this`
- `enrich this list`
- `find IT contacts for these companies`
- `do the weekly run`

For merging:

- `merge these into the master file` ← preferred
- `add these tool exports`
- `combine these CSVs with the master`

---

## When NOT to call the contractor

You can handle these yourself:

- Some companies blank in output → expected, 80-90% is the realistic ceiling
- Phone format differs from what Vtiger expects → use `+91-XX-XXXX-XXXX` format
- A Lusha credit didn't unlock a phone → that company isn't in Lusha's DB, mark "Tried Lusha — not found" in Additional Details

---

## When TO call the contractor

- Claude says "Skill not found" → reinstall via Settings → Skills → Upload
- Coverage drops below 60% for 2 consecutive weeks → may need a research re-pass
- Vtiger import fails → check that CSV is comma-delimited and columns match
- A new tool gets added (e.g., AIPL signs up for another B2B database) → contractor needs to add a parser to Mode C

Contact: [Contractor name / email / phone]

---

## Print + pin this on your desk

The whole week boils down to:

```
MON 10:00 → Upload list → "run AIPL pipeline" → wait → download 4 files
MON 14:00 → Read Coverage Report → call READY rows
TUE 09:00 → Work Action Sheet → unlock 65 contacts → export 4 CSVs
THU 10:00 → New chat → upload 4 exports + master → "merge"
FRI 10:00 → Download updated CSV → Vtiger Import
```
