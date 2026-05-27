# Changelog — AIPL Lead Enrichment Skill

All notable changes to this skill. Following [Keep a Changelog](https://keepachangelog.com/) conventions.

---

## [v5.2] — 2026-05-27

### Added
- **`mca_lookup.py`** — optional OpenCorporates free-tier API integration. Auto-fills Director names + CINs + incorporation dates for cos the rest of the skill missed. Requires `AIPL_OPENCORP_KEY` env var (free signup at https://opencorporates.com/api_accounts/new — 50K calls/mo).
- Graceful no-op when key not set — skill keeps working with no degradation.

### Changed
- Coverage Report's MCA_LOOKUP bucket now includes direct mca.gov.in portal URL + note about the optional auto-lookup.
- `SKILL.md` updated with honest "no free MCA bulk data exists" reality check.

---

## [v5.1] — 2026-05-27

### Added
- **`pipeline_orchestrator.py`** — one-command end-to-end workflow. `detect_intent()` classifies uploaded files (source list vs tool exports vs master). `run()` routes to the right mode automatically. Returns plain-English summary + next action.
- **Mode B Action Sheet** (`Hygienic_Leads_Mode_B_Action_Sheet.md`) — printable per-tool todo list with markdown checkboxes. Auto-allocates 65 free credits across Lusha/Apollo/Signal Hire/Contact Out. Priority-ordered, LinkedIn URLs pre-filled. Eliminates the team's manual "which tool for which company" decision.

### Changed
- `build_files()` now emits 4 artifacts instead of 3 (added Action Sheet).
- `SKILL.md` documents new trigger words: "run AIPL pipeline" / "do the weekly run".

### Workflow impact
- Team weekly workflow: 4 steps → 2 steps.
- Decision-making eliminated: which tool, which mode, which 65 companies.

---

## [v5.0] — 2026-05-26

### Added
- **`local_cache.py`** — SQLite-backed contact cache at `~/.aipl-cache/contacts.db`. Pure stdlib, zero external deps. Schema: companies + contacts + email_patterns + meta (versioned migrations). Soft TTL (180 days) flags stale contacts. Auto-learns email patterns per domain.
- Cache wired into `build_files()` — every run checks cache first, saves fresh enrichments back.

### Performance
- **Cold run:** 30 minutes (4 parallel research agents on 93 cos)
- **Cached run:** 1.1 seconds for same coverage
- **6-month projection:** ~600 cached contacts, ~85% of runs hit cache instantly

---

## [v4.0] — 2026-05-26

### Added
- **`email_finder.py`** — pure-Python email permutation + DNS MX validation. Generates 8 common B2B patterns (`first.last@`, `flast@`, etc.), validates the domain accepts mail. Zero LLM calls. ~1 sec per company. Optional SMTP HELO probe for High-confidence verification.
- `build_vtiger_file.py` auto-calls `email_finder` when row has name + verified website but no email. +20% email coverage on cold runs.

### Removed (explicitly, for ethical reasons)
- **No IndiaMART / JustDial / Tofler / Zauba scraping.** All forbid automated scraping in ToS. India DPDP Act 2023 makes harvesting contact PII without consent chain legally risky.
- **No Google SERP scraping.** Google ToS violation.
- **No LinkedIn data scraping.** Explicit ban + active lawsuits (see Lusha v EU).

### Added
- `SKILL.md` "What you DO NOT do" section explicitly documents the no-scrape policy.
- `SKILL.md` "What you CAN ethically use" section whitelists company websites, annual reports, MCA bulk data, web search snippets, email permutation.

---

## [v3.1] — 2026-05-26

### Fixed
- **`.skill` package was corrupted** — `zip -r` was appending to the existing archive instead of recreating it, so the package contained BOTH old v1 files AND new v3 files. Anyone installing it would get the wrong skill behavior.
- Fix: delete + rebuild `.skill` from scratch each time.

### Changed
- `SKILL.md` "Hard rules" section extended to explicitly cover websites, industries, salutations as no-fabricate fields (not just contacts).
- New rule #4: sanity-check source data (catches leaked emails in Website field).

---

## [v3.0] — 2026-05-26

### Removed
- **`_guess_website()`** — was auto-building `companyname.com` URLs from company names. v2 shipped 48 fake URLs (truncated mid-word, cybersquatter risk, parked domains). Violated the skill's own "never fabricate" rule.
- **"Other / Diversified" industry default** — implied false certainty when really we just couldn't infer. Now leaves blank (honest).
- **Salutation heuristic** ("name ends in 'a' → Ms.") — broke constantly on Indian names like "Sai", "Aditya", "Krishna". Now only set when enrichment explicitly provides one.

### Added
- **`_clean_website()`** — sanitizer that NEVER fabricates. Rejects emails, phone numbers, and non-URL strings that leaked into the Website column from messy source data.

### Verified gain
- Coverage: ~74% named, 30% email, 33% phone (cold).
- Honest output — 0 fabricated URLs, 0 false industry classifications, 0 heuristic salutations.

---

## [v2.0] — 2026-05-26

### Changed
- **Data quality fixes baked into `build_vtiger_file.py`:**
  - Collapsed 24 messy designation strings into 4 IT buckets + 6 Gatekeeper buckets
  - Normalized all phone formats to `+91-XX-XXXX-XXXX`
  - Auto-inferred Industry from company-name keywords (12 industries)
  - Auto-populated Lead Handled by / Assigned To = "Marketing Team"

### Added
- **Actionable Coverage Report** — per-company next-action plan with 7 buckets (READY / CALL_GATEKEEPER / CALL_SWITCHBOARD / MCA_LOOKUP / LUSHA / APOLLO / SKIP). Replaced the old stats dump.

### Removed
- **`build_lookup_queue.py`** — the auto-generated 4-tab Excel was "theatre". Team wasn't going to follow it. Replaced by the actionable Coverage Report.
- **`references/credit-allocation.md`** — 100+ lines of scoring theory nobody read. Replaced by simple 1-page rule in `manual-mode-b.md`.

---

## [v1.0] — 2026-05-26

### Initial release
- Mode A: enrich Indian company list with IT decision-maker contacts
- Mode B: lookup queue for paid-tool free credits (later removed in v2)
- Mode C: merge tool exports back into master
- Vtiger 75-column schema mapping
- Defaults for AIPL marketing (Lead Source, Status, Currency, etc.)

---

## Versioning convention

- **Major (X.0):** breaking change to SKILL.md prompt instructions or core file structure (team needs re-training)
- **Minor (x.Y):** new features or capabilities, backwards-compatible
- **Patch (x.y.Z):** bug fixes, doc updates, no behavior change

## Git tag mapping

| Version | Commit | Date |
|---|---|---|
| v5.2 | `dd841d1` | 2026-05-27 |
| v5.1 | `19040ee` | 2026-05-27 |
| v5.0 | `d4c14cb` | 2026-05-26 |
| v4.0 | `f340ce6` | 2026-05-26 |
| v3.1 | `d79f37c` | 2026-05-26 |
| v3.0 | `29b046c` | 2026-05-26 |
| v2.0 | `ca08eea` | 2026-05-26 |
| v1.0 | `aea1c72` | 2026-05-26 |
