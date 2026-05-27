# Loom Video Script — AIPL Lead Enrichment Walkthrough

**Target length:** 5-6 minutes
**Audience:** Non-technical AIPL marketing team
**Tone:** Friendly, practical, no jargon

**What you need before recording:**
- Screen recording software (Loom, OBS, QuickTime)
- Test company XLSX file open + ready to upload
- Browser tabs open: Claude.ai chat, Vtiger CRM, the Coverage Report from a recent run

---

## SCENE 1 — Intro (30 sec)

> *[Show your face on webcam, Claude.ai chat in background]*

"Hi team — I'm [your name], and this is a 5-minute walkthrough of the AIPL lead enrichment skill.
Here's the deal: what used to take you 4 people about 6 hours each week is now going to take one person about 30 minutes total — and Claude does all the actual research.
Let me show you how it works, end to end."

---

## SCENE 2 — Upload + one command (45 sec)

> *[Screen-share Claude.ai. Show the chat input box.]*

"Step one — Monday morning. Open Claude.ai, start a new chat.

> *[Click paperclip icon, select XLSX file]*

Drag in your week's new company list. The file should have columns like EnterpriseName, Address, State, District, Pincode — same format you've always used.

> *[Type in chat]*

Then type three words: **'run AIPL pipeline'**.

That's literally the whole prompt. Hit Enter."

---

## SCENE 3 — What Claude does (45 sec)

> *[Show the chat running, scrolling through tool outputs]*

"Behind the scenes, Claude is:
- Reading your file
- Web-searching each company for IT Heads, CTOs, IT Managers
- Falling back to MCA filings if it can't find an IT person
- Checking our local cache from prior runs — so re-research time drops 10x for cos we've seen before
- Generating the final files in Vtiger's exact import format

For a 100-company list, this takes about 15-25 minutes. Go grab a coffee.

> *[Skip ahead to the result message]*

When it's done, Claude shows a summary — number of contacts found, coverage breakdown, and 4 files to download."

---

## SCENE 4 — The 4 outputs (60 sec)

> *[Show the Coverage Report opened in a text editor]*

"Let's look at what you get.

**File 1: Hygienic_Leads.xlsx** — your lead data in Vtiger's exact 75-column format. Open it in Excel to spot-check, but don't edit it — Vtiger will reject changed formatting.

**File 2: Hygienic_Leads.csv** — same data as comma-CSV. This is what you upload to Vtiger.

**File 3: Coverage_Report.txt** — this is your roadmap.

> *[Scroll through the report]*

See these buckets? READY TO CALL — call these today, they're complete. Call gatekeeper — call the Director, ask for IT Head. Cold-call switchboard — these are blanks, search JustDial. Use Lusha credit, Use Apollo credit — these are what we'll do Tuesday.

**File 4: Mode B Action Sheet** — this is the magic.

> *[Open the Action Sheet markdown]*

Look at this — it's literally a checklist. 'Open Lusha, look up these 33 companies'. 'Open Apollo, look up these 8.' We've already decided which tool for which company so you don't have to think about it. Just tick the box as you finish each one."

---

## SCENE 5 — Working the Action Sheet (60 sec)

> *[Show the Lusha browser extension, then click through one example]*

"Tuesday morning — open the Action Sheet, open your Lusha browser extension.

Go down the list. For each company, look it up in Lusha, click 'Reveal phone', export to CSV when you're done with all 40.

Same for Apollo — look up the 8 companies it tells you, export to CSV. Same for Signal Hire and Contact Out.

> *[Show 4 CSVs saved to desktop]*

By Tuesday afternoon, you have 4 export CSVs from the 4 tools."

---

## SCENE 6 — Merge (45 sec)

> *[Switch to a fresh Claude.ai chat]*

"Thursday — open a NEW Claude chat. Upload all 4 export CSVs from Tuesday + your master Hygienic_Leads.xlsx from Monday.

> *[Drag-drop all files]*

Then type: **'merge these into the master file'**.

> *[Show Claude detecting tools + merging]*

Claude auto-detects which CSV came from which tool. Merges everything into the master without overwriting your verified data. Spits out an updated CSV."

---

## SCENE 7 — Vtiger import (30 sec)

> *[Switch to Vtiger CRM]*

"Friday — log into Vtiger, go to Leads, Import.

> *[Click Import, upload the CSV]*

Upload `Hygienic_Leads_Updated.csv`. Vtiger auto-maps all columns. Click Import. Done.

> *[Show import success message]*

That's it. 95% lead coverage, every contact has a source URL, the team is ready for outreach."

---

## SCENE 8 — Outro (30 sec)

> *[Back to webcam]*

"Quick reminders:

- The whole week is about 90 minutes of YOUR time, vs the 24+ hours it used to take
- Read the Runbook PDF for a printable step-by-step
- The Troubleshooting doc covers most issues — check it before calling me
- This skill keeps getting smarter as you use it — every contact you verify gets cached for next time

Questions? Ping me. Otherwise, give it a try this week and let me know how it goes."

> *[End recording]*

---

## Recording tips

- **Speak slowly.** Indian internet means non-native English users will pause/replay.
- **Show, then explain.** Click first, talk about what just happened second.
- **Don't apologize for length.** 5 min is fine — they'll watch in chunks.
- **Hindi subtitles?** Optional but recommended. Loom auto-generates captions; download them, paste into a translator (DeepL works well), upload the translated SRT.
- **Re-record any sentence you stumble on.** Loom lets you cut + restart per take.

---

## What to NOT include

- ❌ Tech jargon ("API", "regex", "JSON")
- ❌ Anything about the SQLite cache schema
- ❌ Apology language ("Sorry, this is complicated...")
- ❌ Future features that aren't shipped yet
- ❌ Cost comparisons vs paid tools (that's the leadership brief, not the team's concern)

---

## After publishing

- Upload to Loom + share link with team via WhatsApp/email
- Pin the Loom link in the team's Slack/Discord/whatever they use
- Add to AIPL's internal training portal if they have one
- Reference link in `02_TEAM_RUNBOOK.md` section header
