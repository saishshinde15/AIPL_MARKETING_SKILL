# Handoff Documentation — AIPL Lead Enrichment Skill

Pick the doc that matches your role.

| If you are... | Read this | Time |
|---|---|---|
| **AIPL leadership / CEO** | [`01_LEADERSHIP_BRIEF.md`](01_LEADERSHIP_BRIEF.md) | 5 min |
| **AIPL marketing team** (running the skill weekly) | [`02_TEAM_RUNBOOK.md`](02_TEAM_RUNBOOK.md) | 10 min + print |
| **Onboarding a new team member** | [`03_LOOM_VIDEO_SCRIPT.md`](03_LOOM_VIDEO_SCRIPT.md) | watch the 5-min video |
| **Something broken / weird output** | [`04_TROUBLESHOOTING.md`](04_TROUBLESHOOTING.md) | scan + find the symptom |
| **Curious about version history** | [`05_CHANGELOG.md`](05_CHANGELOG.md) | reference |

---

## Quick start (1 minute)

1. Install the skill: download `aipl-lead-enrichment.skill` from the repo root → Claude.ai → Settings → Capabilities → Skills → Upload
2. Open a new Claude chat → drop in your company XLSX → type **`run AIPL pipeline`**
3. Download the 4 generated files
4. Follow the Action Sheet to spend your 65 free monthly credits
5. Merge tool exports back when done → Vtiger import

Full step-by-step in the [Team Runbook](02_TEAM_RUNBOOK.md).

---

## What the skill does in one sentence

> Takes a list of Indian companies, finds IT decision-maker contacts via public sources, outputs a Vtiger-ready CSV plus a printable per-tool todo for the team's free-tier paid credits — all in 30 minutes of human time per week.

---

## Architecture (for the technically curious)

```
User (Claude.ai chat)
    │
    │ uploads company list
    ▼
┌─────────────────────────────────────────────┐
│  aipl-lead-enrichment skill (SKILL.md)      │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │ pipeline_orchestrator.py               │ │
│  │   - detect_intent(files)                │ │
│  │   - routes Mode A vs Mode C             │ │
│  └────────────────────────────────────────┘ │
│              │                               │
│              ▼                               │
│  ┌────────────────────────────────────────┐ │
│  │ Mode A: build_vtiger_file.py           │ │
│  │   1. Check local_cache for prior data  │ │
│  │   2. Web search (Claude does this)     │ │
│  │   3. email_finder.py for missing emails│ │
│  │   4. mca_lookup.py (optional) for blanks│ │
│  │   5. Generate 4 output files            │ │
│  └────────────────────────────────────────┘ │
│              │                               │
│              ▼                               │
│  ┌────────────────────────────────────────┐ │
│  │ Outputs:                                │ │
│  │   - Hygienic_Leads.xlsx                 │ │
│  │   - Hygienic_Leads.csv                  │ │
│  │   - Coverage_Report.txt                 │ │
│  │   - Mode_B_Action_Sheet.md              │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │ Mode C: merge_tool_exports.py          │ │
│  │   (when team uploads tool exports)      │ │
│  │   1. Auto-detect tool format           │ │
│  │   2. Fuzzy-match companies              │ │
│  │   3. Backfill without overwriting       │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
              │
              ▼
       ~/.aipl-cache/contacts.db
       (local SQLite — grows with use)
```

---

## Repo structure

```
AIPL_MARKETING_SKILL/
├── aipl-lead-enrichment.skill          # ← upload this to Claude.ai
├── aipl-lead-enrichment/               # source files (for editing)
│   ├── SKILL.md                        # main prompt instructions
│   ├── scripts/
│   │   ├── build_vtiger_file.py        # Mode A core
│   │   ├── merge_tool_exports.py       # Mode C
│   │   ├── pipeline_orchestrator.py    # one-command router
│   │   ├── local_cache.py              # SQLite flywheel
│   │   ├── email_finder.py             # permutation + MX validation
│   │   └── mca_lookup.py               # optional OpenCorporates
│   ├── references/                     # docs Claude reads as needed
│   │   ├── vtiger-schema.md
│   │   ├── enrichment-sources.md
│   │   ├── manual-mode-b.md
│   │   └── target-roles.md
│   └── assets/
│       └── vtiger_template_headers.tsv
└── docs/                               # this folder — handoff package
    ├── 01_LEADERSHIP_BRIEF.md
    ├── 02_TEAM_RUNBOOK.md
    ├── 03_LOOM_VIDEO_SCRIPT.md
    ├── 04_TROUBLESHOOTING.md
    └── 05_CHANGELOG.md
```
