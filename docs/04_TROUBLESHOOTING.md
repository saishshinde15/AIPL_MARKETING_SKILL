# Troubleshooting Guide — AIPL Lead Enrichment Skill

**Use this FIRST** before contacting the contractor. 90% of issues are covered here.

---

## "Claude doesn't seem to know what 'AIPL pipeline' means"

**Most likely cause:** Skill isn't installed in this Claude account.

**Fix:**
1. Go to https://claude.ai → click profile icon (top-right) → **Settings**
2. Click **Capabilities** → **Skills**
3. Check if `aipl-lead-enrichment` is in the list with a green checkmark
4. If not: click **Upload skill** → upload `aipl-lead-enrichment.skill` from the shared drive
5. Confirm install → start a new chat → try again

**If still not working:** the file might be corrupt. Download a fresh copy from:
https://github.com/saishshinde15/AIPL_MARKETING_SKILL → click `aipl-lead-enrichment.skill` → **Download raw**

---

## "Claude says my file format is wrong"

**Most likely cause:** missing the expected column headers.

**The skill needs:** `EnterpriseName` (or `Company`), `Address`, `State`, `District`, `Pincode`

**Fix:**
1. Open your XLSX in Excel
2. Rename column headers if needed (e.g., `Company Name` → `EnterpriseName`)
3. Make sure all 5 columns are present (can be blank but must exist)
4. Save → re-upload

---

## "Coverage dropped from 80% to 40% this week"

**Most likely causes:**

**A) The new list has different geography** — companies outside Mumbai/Pune/Thane have less web presence
- Check what cities are in the list
- Outside Maharashtra, expect 50-60% coverage instead of 80%

**B) Lots of brand-new Pvt Ltds** — incorporated 2024-2025 → not yet on Zauba/Tofler
- Check Additional Details column for "incorporated 2024" / "incorporated 2025"
- These need MCA portal manual lookup

**C) Claude.ai had an outage during your run**
- Check status.anthropic.com
- Re-run when it's green

**Action:** if coverage is low for a legit reason, just note it in the Coverage Report and proceed. The skill output is still good for the rows it found.

---

## "Lusha browser extension isn't showing the company"

The Action Sheet pre-decides which company goes in which tool. If Lusha doesn't have it, **that's expected** for ~20-30% of Indian SMEs.

**Fix:**
1. Mark the row "Tried Lusha — not found" in Additional Details
2. Try the same company in Apollo or Signal Hire
3. If nothing works → cold-call the switchboard via JustDial

**Don't try multiple tools on the same row** — that wastes your monthly free credits.

---

## "I imported the CSV into Vtiger and 90% of rows have errors"

**Most likely cause:** you opened the CSV in Excel first → Excel changed phone formats / removed leading zeros / stripped special chars.

**Fix:**
1. **DON'T open CSV in Excel before Vtiger import.** Excel mangles Indian phone numbers (drops the leading `+91-`).
2. Re-download the CSV directly from Claude → upload to Vtiger without opening
3. If you need to review the data first, use the **XLSX** file (Excel-safe), and import the **CSV** to Vtiger separately

---

## "Vtiger says 'Lead Source value invalid'"

**Most likely cause:** Vtiger has a custom Lead Source dropdown that doesn't include `Master DB`.

**Fix (one-time):**
1. In Vtiger: Settings → Module Layouts → Leads → Lead Source field
2. Add `Master DB` to the options list
3. Save → re-import

OR change the default in the skill to whatever Vtiger expects (contact contractor).

---

## "The merge step is overwriting good data with blanks from Lusha"

**Shouldn't happen** — the skill explicitly preserves non-empty master fields. If you see this:

1. Check that you uploaded the **most recent** master Hygienic_Leads.xlsx (not last week's)
2. Check that the company names in the Lusha export match the master (sometimes Lusha returns slightly different spelling)

**Workaround if it happens once:**
1. Open the updated CSV in Excel
2. Compare against your prior week's master
3. Manually restore any overwritten cells
4. Report to contractor — this is a bug

---

## "I unlocked 40 Lusha contacts but the export CSV only has 12 rows"

Lusha's free tier exports only the **unlocked** contacts. If you only revealed 12 phones (because some weren't available), only 12 will export.

**This is normal.** Lusha's "40 credits" means you can ATTEMPT 40 unlocks, but each unlock isn't guaranteed to return data.

**Action:** continue with the 12 you got. Don't try to re-unlock failures.

---

## "Claude is taking forever on a single company"

The skill normally takes ~10-30 seconds per company. If it's stuck:

1. Watch for the "..." indicator — Claude is still working
2. If >2 min on one company → it's likely doing deep MCA fallback. Be patient.
3. If >5 min on one company → something's wrong. Reload the chat, try again.

---

## "How do I know if the cache is working?"

Your second run of the same file should take **~1 second** instead of 30 minutes. If it doesn't:

1. The skill might not be reading from the same machine's cache (e.g., if you ran first on your laptop, now on a different one)
2. The cache lives at `~/.aipl-cache/contacts.db` on whichever machine ran the skill last
3. Cache is per-user, per-machine — not shared across the team yet

**If you want shared team cache:** contact the contractor — easy upgrade to a cloud DB.

---

## "Where's the cache stored? Can I back it up?"

- **Location:** `~/.aipl-cache/contacts.db` (on macOS/Linux) or `%USERPROFILE%\.aipl-cache\contacts.db` (Windows)
- **Format:** SQLite database, ~few MB
- **Backup:** copy the `.db` file to Google Drive / Dropbox / company shared drive
- **Restore on a new machine:** copy the `.db` file to the same location on the new machine

---

## "I want to delete a wrong contact from the cache"

Open SQLite browser (free download: https://sqlitebrowser.org), open the `.db` file, run:

```sql
DELETE FROM contacts WHERE first_name = 'Wrong' AND last_name = 'Person';
```

Or just contact the contractor — they can do it in 2 minutes.

---

## "OpenCorporates says my API key is invalid"

You probably:
- Typo'd the key when setting the env variable
- Used a paid-tier key that expired
- Got rate-limited by accident

**Fix:**
1. Re-check the key at https://opencorporates.com/users/me
2. Re-set: `export AIPL_OPENCORP_KEY="your_token_here"` (in a terminal before starting Claude)
3. If still failing → run without the key (skill silently no-ops the MCA module)

---

## "I want a brand-new clean run, no cache"

In a terminal:
```bash
rm ~/.aipl-cache/contacts.db
```
Then re-run the skill. It'll start fresh.

**Warning:** this wipes ALL prior verified contacts. Only do it if you really want a clean slate.

---

## When to contact the contractor

Only when:
- ✅ You've tried the fixes above + still broken
- ✅ The skill output is fundamentally wrong (e.g., fabricated data showing up)
- ✅ Coverage drops below 60% with no explanation
- ✅ You want to add a new feature (e.g., parse a 5th paid tool's exports)
- ✅ Vtiger schema changes (new column added, etc.)

**Don't contact for:**
- ❌ "I'm not sure what to do" → re-read the Runbook
- ❌ "How do I install the skill?" → see top of this doc
- ❌ "Should I use Lusha or Apollo?" → the Action Sheet tells you
- ❌ "Some companies are blank" → expected, 80-90% is the ceiling

Contact: [Contractor name, email, phone]

Response time: usually within 24 hrs business days.
