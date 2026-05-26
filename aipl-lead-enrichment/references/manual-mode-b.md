# Manual Mode B — Paid Tool Lookup Guide

This is the **manual playbook** the marketing team follows when working through the `Hygienic_Leads_Coverage_Report.txt` output. We don't auto-generate a fancy 4-tab lookup queue any more — that was theatre. The team can't open Lusha/Apollo/Signal Hire/Contact Out browser extensions from Claude anyway, so we keep this as a simple decision rule the team memorizes in 2 minutes.

---

## The rule (read this once, internalize it)

For each company in the Coverage Report, look at what gap you're filling, then pick the tool:

| What you need | Which tool to use | Why |
|---|---|---|
| **Phone number** | **Lusha** | Best Indian mobile coverage. 40 free credits/month. |
| **IT-role email at a large enterprise** | **Apollo** | Best for filtering by job title. 10 credits. |
| **Senior decision-maker bundle** (name + email + phone, single unlock) | **Signal Hire** | Best for VP/CXO targets. 5-10 credits. |
| **Email when you already have a LinkedIn URL** | **Contact Out** | Specialized LinkedIn-to-email scraper. 10 credits. |

---

## Priority order — work the Coverage Report top to bottom

The Coverage Report groups companies into these buckets, **in order of where to spend your time**:

1. **✓ READY TO CALL DIRECTLY** — IT contact with email + phone is already in hand. **Call them today.** Zero tool credits needed.
2. **↻ CALL THE GATEKEEPER** — You have an MD/Director with phone. Call them and ask: *"May I please speak to your IT Head or IT Manager?"* Costs nothing, often gives you the IT name + extension immediately.
3. **☎ COLD-CALL SWITCHBOARD** — Pure blanks. Search the company name on [JustDial](https://www.justdial.com), get the switchboard number, call, ask for IT. ~70% of the time this works.
4. **💳 USE LUSHA / APOLLO CREDIT** — Use paid-tool credits ONLY for companies in these two buckets. Don't waste credits on blanks the switchboard call could solve.

---

## Hard rules

- **Don't burn credits on bucket 3 (switchboard) before trying the call.** A 2-minute phone call is free; a Lusha credit isn't.
- **Don't burn credits on bucket 2 (gatekeeper) at small Pvt Ltds.** If it's a 20-person company, the MD IS the IT decision-maker. Just call them.
- **65 credits / month total** — Lusha 40, Apollo 10, Signal Hire 10, Contact Out 10. Allocate proportionally to bucket sizes.
- **Mark each row as you unlock** in your own tracker (Notion / Excel / whatever) so you know what's done.

---

## After all the manual unlocks: Mode C

Export each tool's results to CSV. Open a new Claude chat. Upload all the CSVs + the current master file. Say:

> *"merge these tool exports into the master file"*

The skill's Mode C does the rest — auto-detects which tool each CSV is from, fuzzy-matches by company name, backfills empties **without overwriting verified data**, re-emits the final Vtiger-ready files.
