# Changelog — AIPL Lead Enrichment Skill

All notable changes to this skill. Following [Keep a Changelog](https://keepachangelog.com/) conventions.

---

## [v8.2] — 2026-06-08

### Changed — Email is now person-direct + tiered, never a role inbox
The biggest quality fix yet. The old logic preferred "any real published email,"
which for regulated firms meant `grievance@` / `gro@` / `care@` / Company-Secretary
inboxes — a complaints desk, useless for sales (on a real insurance run, **55% of
emails were these role inboxes**). v8.2 inverts it:
- **`grievance@`/`info@`/`care@`/`gro@`/`*service`/`*support` are auto-detected and
  BANNED from Primary Email** — parked in Additional Details as a fallback only.
- New tiered waterfall: cache (`Verified — own data`) → published-harvest
  (`Confirmed — published`) → **derive ONLY from a cache-proven pattern**
  (`Verified-pattern`) → honest blank + intel. Every email carries an
  `EMAIL CONFIDENCE:` tag.
- **An address is derived only where the team's own data proves the domain's
  pattern** (≥1 real example). No blind pattern-guessing — that line was set with
  the user and is enforced in code. No proof → blank + a "where to finish it" note.
- Result on the insurance file: role inboxes in Primary Email **55% → 0%**, 49
  person-direct emails all tiered (35 derived from proven patterns, 14 published).

### Added
- **`scripts/ingest_hygienic.py`** — pours a team-built hygienic DB (real
  name+email columns) into the cache and learns each domain's email pattern.
  **Structure-agnostic: detects columns by CONTENT, not header names**, so it
  survives the team's ever-changing file shapes (renamed/typo'd headers like
  "Mail id" / "Desgination", blank/category columns). A raw company list (no email
  column) correctly ingests nothing. Tested: the team's 02.06 insurance DB →
  190 verified emails + 52 confirmed patterns cached.
- `build_vtiger_file.py`: `_is_role_inbox`, `_derive_email`, `_email_domain`,
  `_base_domain` (subdomain → registrable-domain pattern fallback), and the tiered
  resolver wired into `_build_row` (now takes the cache).
- SKILL.md: rewritten EMAIL step (person-direct waterfall + tiers + DPDP rule +
  exhibitor-directory/published-harvest as the primary source).

### Note
- Rollback point: **v8.1** is the last release before the email engine. If v8.2
  misbehaves, reinstall the v8.1 release. v8.2 is purely additive to it.

---

## [v8.1] — 2026-06-08

### Added — Batched real-research workflow is now part of the skill
- **`scripts/merge_research_chunks.py`** — reusable, deterministic merge that
  stitches batched research results back onto the source file's EXACT company
  names so `build_files()` can find each one. The hardened `core()` matcher
  reconciles what used to silently blank rows: legal-form suffixes, "(formerly …)"
  / "(CIC)" parenthetical notes, dd-mm-yyyy / "w.e.f" date noise, **spaced-out
  acronyms** ("H D F C" → HDFC), minor typos ("Somp" → Sompo, "Aegeon" → Aegon),
  and **true duplicates** (a company listed twice). Optional `extra_stop` lets a
  sector-uniform list (all-Insurance, all-NBFC) match on the distinctive part.
  Importable `merge(companies, chunks, extra_stop=…) -> (enrichment, report)`,
  plus a `--selftest` and a CLI match-report. Self-test + a real 89-company
  insurance list both reconcile **100%**.
- **SKILL.md** — new "Big lists — batched real research (the 'no-cheating' mode)"
  section documenting the chunk→research→merge→build loop for 40+ company lists.

### Honesty note baked into the skill
- The new section states plainly that the **Claude.ai app has no sub-agents**, so
  it runs the research batches **sequentially** (same quality/coverage as a
  Claude Code parallel run, just slower and bounded by the message budget). The
  **merge step is identical and free everywhere** — that's what makes the output
  reproducible regardless of where the skill runs. No promise that the app
  matches Claude Code on *speed*; only on *result*.

### Proven on real runs
- Insurance list (89 cos, all operating insurers/TPAs/brokers): **92% named,
  98% callable, 96% email (93% real-published), 78% with a named IT
  decision-maker** — vs ~21% on the older NBFC holding-SPV list. Same engine;
  the difference is operating companies vs non-operating holding shells.

### Note
- Tags v6.1 → v8.0 shipped on GitHub without individual changelog entries; v8.0
  was the consolidated stable release (bulletproof input, structural sizing,
  3-tier phone backup, real-email harvesting, real-title designations). v8.1
  builds directly on it.

---

## [v6.0] — 2026-05-27

### Added — Sales enablement layer (the "different product" pitch)
- **`sales_priority.py`** — Hot/Warm/Cold/Skip scoring per row (35-point scale: size + industry + role + data completeness). Stamped into Vtiger `Source Campaign` field.
- **`cold_call_scripts.py`** — Per-company 30-second phone scripts. 12 role-specific opener templates × 10 industry value props. Switchboard script for blank rows. 4 objection handlers per call.
- **`email_templates.py`** — Per-contact-with-email 4-line cold-email templates. Industry-tailored subjects + bodies. Ready to copy-paste-send.
- **`lead_brief.py`** — Top-20 1-page sales-execution kits per Hot lead. Company snapshot + best contact + recommended channel + inline phone script + inline email + sources. Print-ready Markdown.

### Added — Robustness layer (handles inconsistent input)
- **`schema_detector.py`** — Auto-detects 50+ column name variants. Maps `Company`/`EnterpriseName`/`Organization`/etc. to canonical schema.
- **`data_sanitizer.py`** — Fixes pincode .0 suffix, state abbreviations, "PR IVA TE" typos, multi-space collapse, address newline cleanup. Tested: 211 cells auto-sanitized on AIPL's 93-co list.
- **`company_classifier.py`** — Classifies each company: Pvt Ltd / Public Ltd / LLP / Cooperative / Nidhi / Producer Co / OPC / Section 8 / Partnership. Routes each type to appropriate research strategy (skip Cooperatives, enhanced research for listed Public Ltd, etc.).

### Changed
- `build_files()` now emits 7 artifacts (was 4): XLSX + CSV + Coverage_Report + Action_Sheet + Phone_Scripts + Email_Templates + Lead_Briefs.
- Every Vtiger row stamped with Hot/Warm/Cold tag in Source Campaign field.
- `pipeline_orchestrator` auto-runs schema detection + data sanitization on every input file.

### Tested on AIPL's 93-co list
- 211 cells auto-sanitized (pincodes, state abbreviations, address whitespace)
- Priority: 6 Hot / 56 Warm / 26 Cold / 5 Skip
- 72 phone scripts generated
- 50 email templates generated
- Top 20 Lead Briefs generated
- Run time: ~2 seconds end-to-end on cached data

### THE PITCH FOR AIPL (vs Apollo+Lusha)
Apollo+Lusha give you raw contact data for ₹10K/mo. v6 gives you contact data
PLUS personalized phone scripts PLUS personalized emails PLUS Hot/Warm/Cold
prioritization PLUS top-20 lead briefs — for ₹1,700/mo. Different product.

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
