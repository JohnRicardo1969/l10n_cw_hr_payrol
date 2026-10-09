# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

This is the design/planning repository for **`l10n_cw_hr_payroll`**, an Odoo 19 Enterprise payroll localization module for Curaçao (country code `cw`). **No module code exists yet** — the repo currently holds the specifications the code will be built from. There is no `__manifest__.py`, no Python, and therefore no build/lint/test workflow. When implementation begins, the module is built on top of Odoo's Enterprise `hr_payroll` engine and is intended to run on **Odoo 19 Enterprise / Odoo.sh** (SaaS is explicitly unsupported — custom modules and Python salary rules are required).

### Source-of-truth documents

Read these before designing or implementing anything; they are authoritative and self-consistent except where flagged below.

- `docs/prd/PRD - v3.0D.md` — Product requirements for the v1.0R release (monthly payroll only). Scope, data models, the canonical salary-rule sequence, rate tables, lifecycle, accounting, acceptance criteria, roadmap.
- `docs/tech_design_l10n_cw_hr_payroll_v3.0D.txt` — Full technical design (the PRD's source). Contains field-level model definitions, salary-rule Python listings, and the file tree.
- `_bmad-output/planning-artifacts/architecture/.../.memlog.md` — The distilled **architecture spine**: the binding invariants (ADs) every salary rule and model must obey. This is the highest-signal file for implementation decisions.
- `docs/*.pdf` — Official 2026 Belastingdienst Curaçao (loonbelasting schijventarief, bijzondere beloningen, lookup tables) and SVB (premiums) publications. These are the statutory ground truth; calculations must reconcile to them within XCG 0.02.
- `docs/figure-0{1,2,3}-*.png` — Module dependency architecture, three-tier wage component model, payroll run lifecycle.

`_bmad/` and `.claude/` are gitignored BMad/tooling scaffolding, not project source.

### Spec-sync discipline (MANDATORY)

Any decision made while working on epics, stories, or implementation that changes a requirement, a statutory rule, a model, a dependency, or an architecture invariant MUST be applied to **all living spec documents in the same working session**, never deferred:

- `docs/prd/PRD - v3.0D.md` — the PRD
- `_bmad-output/planning-artifacts/architecture/.../ARCHITECTURE-SPINE.md` (+ its `.memlog.md`) — the architecture spine
- `_bmad-output/planning-artifacts/epics_EN-<YYYYMMDD>.md` **and** `epics_NL-<YYYYMMDD>.md` (currently `-20261008`) — the epics/stories pair (bilingual lockstep). The date in the name is the **last update date**: when the epics change on a new date, rename both files to that date and update every live reference (this file, the NL `translationOf:` frontmatter, story files that are not yet done); leave references in point-in-time records as they are (convention added 2026-10-08; renamed from `Odoo Module Design Epics - EN/NL - v1.0D.md`)
- This file (CLAUDE.md), where a stated convention changes

Add a dated supersession note at each edit (e.g. "decided 2026-07-07, superseding …"). **Excluded** (point-in-time records — never retro-edit): `docs/tech_design_l10n_cw_hr_payroll_v3.0D.txt` and historical review artifacts; the spine rules their literals superseded. Precedents: the category decision, the F1–F3 readiness reconciliations, and the `hr_contract`→`hr.version` (D1) ripple were each applied across the full chain in one pass.

## What the module does

Implements the complete Curaçao statutory payroll framework (loonbelasting + SVB premiums: AOV/AWW, AVBZ, BVZ, ZV, OV) entirely inside Odoo, with no external payroll service. The calculation is a fixed sequence of `hr.salary.rule` records (Seq 10–150) mirroring the official Curaçao payroll pseudocode, one rule per step. v1.0R is **monthly payroll only**; other pay periods and many features are deferred (see PRD roadmap). **Cessantia is permanently out of scope** — if ever reinstated, its rule, GL accounts, and the journal balance formula must change together.

## Architecture invariants

These are binding. Most calculation bugs come from violating one of them; the `.memlog.md` is the full list with rationale.

- **Three layers, dependencies point inward toward Localization.** *Localization* (statutory definitions + data: `hr.salary.rule` extension, `CWMONTHLY`/`CWSTAFF` structures, the CW rules, `hr.tax.bracket`, employee toeslag fields, contract OV%) ← *Application* (config/workflow: `hr.wage.component.set`(+line), `hr.employee.wage.line`, `hr.wage.component.ytd`, apply wizard, views/menus/security) ← *Reports* (QWeb PDF + CSV; **read-only, compute nothing**). A report must never recompute a statutory amount.
- **Strict sequence + reference discipline.** Rules evaluate in ascending sequence (10→150). A rule may reference only *prior* results (`rules.CODE.amount`, `categories.X`) — never a later rule.
- **Sign convention.** Deduction/employee-premium rules return **negative** amounts; employer-cost and base rules positive. `NET` sums `BASIC + ALW + DED` directly relying on `DED` being negative. Employer contributions go to category `ER` and are **excluded** from NET. Overtime goes to `ALW`. **Exception — BVZ (decided 2026-10-08, superseding BVZ_ER in `ER`):** the employer BVZ supplement is an untaxed `ALW` earning paid to the employee (`BVZ_SUPPL`, inside NET) and the **total** BVZ premium is a `DED` line (`BVZ_TOTAL`); `TOTAL_ER_COST` still counts the supplement. Untaxed earnings (art. 6F LLB) are `ALW` lines flagged `is_untaxed`, excluded from `TAX_INC` and the AOV/AWW, BVZ and AVBZ bases; the separate `NONTAXED` rule (Seq 140) is removed (AD-27).
- **Ceilings — monthly maximum, except BVZ (AD-24 revised; decided 2026-10-08, superseding the cumulative method for AOV/AWW and AVBZ of 2026-07-08).** AOV/AWW (incl. the 1% surcharge on the monthly excess), AVBZ, ZV and OV are capped **per month** (annual ceiling ÷ 12; ZV/OV their monthly cap); each month stands alone and differences are settled through the employee's annual assessment. **BVZ only** uses a running total on the premium **base**: base this period = min(premie-loon so far this year, 150,000 × months since insurance/employment start ÷ 12) − base already used; premium and supplement = that base × **this period's** rates (segment-wise, so a mid-year AOV-insured change never re-rates earlier months). Reopening a period cascades forward for BVZ only. Never ×12→÷12. The shared premium bases (`*_PREM_INC`) stay **uncapped**; each premium rule applies its own cap. Loonbelasting reads the period-specific lb-maandtabel directly (AD-20).
- **Dated-rate authority — rates are data, never literals (AD-5/AD-22).** *All* statutory rates, ceilings and thresholds are **append-only** dated data (expire via `valid_to`, insert a new `valid_from`; never delete), held in three stores: **SVB premiums and ceilings** in one per-year `hr.svb.parameters` record (each ceiling stored once; includes the BVZ pensioner rate and the 2.8% pensioner supplement); the **bijzondere-beloningen rates and the Belastingdienst scalars** (basiskorting, verwervingskosten, toeslagen) in `hr.tax.bracket` keyed by `tax_type`, read via `compute_tax()` / `lookup_marginal_rate()`; and **loonbelasting** in the official lb-tabel (`hr.loonbelasting.tabel` + `.lijn`, AD-20). The v3.0D salary-rule *listings* hardcode literals (9.3%, 6.5%, 9.5%, ceilings, 606247.08, 41.67, 2915); these are superseded — no rate literal in rule Python, because rate changes must not require a code deploy. (Corrected 2026-10-08, superseding the earlier wording that put SVB premiums in `hr.tax.bracket` with per-(insurance, payer) `tax_type` values.)
- **Enable/disable gate + never-gate list.** Each premium/tax rule checks its `hr.employee.wage.line.enabled`; if `False`, set `result = 0.00` and skip its logic (downstream gets `0.00`, never an error/stale value). The **never-gate** rules always execute regardless of flags because they are shared bases/outputs: `BVZ_PREM_INC`(20), `AOV_PREM_INC`(50), `TAX_INC`(80), `LOONBEL_RAW`(90), `NET_PRE`(125), `NET_CARRY`(128), `NET`(130), `TOTAL_ER_COST`(150) (`NET_PRE`/`NET_CARRY` added 2026-10-08).
- **`active` vs `enabled` are independent.** `active=False` hides from UI **and** excludes from calc. `enabled=False` keeps the line **visible for audit** but returns `0.00`. A statutory exemption for audit = `active=True, enabled=False`.
- **Employee-level dated wage lines (AD-25, decided 2026-10-08).** Recurring per-employee items (Bijtelling, generic earnings, untaxed earnings, beschikkingsaftrek, net deductions) are Tier-3 wage lines with a `date_from`/`date_to` validity window, edited **in place** when something changes; payroll reads the line as it is at calculation time and the dates only decide whether it applies to the period. Per-period payslip inputs remain only for overtime hours, bijzondere beloningen and `PENSION_EMP`.
- **Three-tier decoupling.** Applying a Tier-2 `hr.wage.component.set` to employees is a **one-time copy** (via the apply wizard) into independent Tier-3 `hr.employee.wage.line` records. Later edits to the set do **not** propagate. `hr.employee.wage.line.salary_rule_id` is read-only after creation.
- **Single state-commit point.** `hr.payslip.run.action_close()` is the *only* place results are committed: confirm+lock payslips → upsert `hr.wage.component.ytd` (increment per line) → post the `account.move` (draft→posted) → expose run reports. YTD and the journal are mutated nowhere else. The same holds for the close-time state added 2026-10-08 (AD-29): net carry-over balance, net-deduction balances, lifetime cumulative-cap accumulators, one-time wage-line resets, beschikking zeroing and the year lock (set by marking a run as the last of the year, with confirmation). Controlled reopen must reverse each of them; it applies to monthly runs of an unlocked year only. A **locked year is never reopened in the module**: the only route is restoring the Odoo.sh backup taken before the year's last run and redoing it (decided 2026-10-08). Recompute (herberekening) is allowed only **pre-close**; closed periods are corrected only through correction lines on the current payslip (AD-30).
- **Accounting balance by construction.** Every employer-cost debit has a matching payable credit; total debit == total credit follows from the NET identity (total loon = net + all employee deductions). Net deductions credit a payable per creditor and GL account, and a net carry-over is an employee receivable (AD-10, 2026-10-08). GL account numbers in the design are **indicative placeholders**, mapped per company at onboarding (v1.1R) — not requirements.
- **Money/rounding.** Currency XCG; `compute_tax` returns `round(x, 2)`; acceptance tolerance is XCG 0.02 (rounding only). `compute_tax` returns **raw** loonbelasting; toeslagen are applied *afterward* as **monetary deductions from the tax amount** (not as taxable-income reductions), floored at 0.

## Resolved decisions and open questions

**Resolved — overtime in the premium base (AD-14).** The v3.0D source was internally contradictory (`BVZ_PREM_INC` excluded overtime; `AOV_PREM_INC` included it). The product owner confirmed (2026-06-26) that overtime **is** included. All premium bases derive from `categories.BASIC + categories.ALW`, and `BVZ_PREM_INC` must be refactored off `rules.TOTAL_LOON.amount` to that base. No longer a blocking question.

No blocking questions remain for v1.0R. The other open questions (OQ-01..OQ-23; OQ-13..OQ-23 added 2026-10-08) are non-blocking — see the PRD; deferred items are tracked in the architecture spine's Deferred section.

## Conventions when code is added

- Manifest: version `19.0.0.1.0`, category `Human Resources/Payroll` (matches all shipped `l10n_*_hr_payroll` modules — keeps the future official-localization track open; supersedes the v3.0D `Accounting/Localizations/Payroll`, decided 2026-07-07), license `OPL-1`, country `cw` (manifest key `countries: ['cw']`), installable, not auto-installed. Direct depends: `hr`, `hr_holidays`, `hr_payroll`, `hr_payroll_account`, `hr_attendance` — **no `hr_contract`**: the module was removed in Odoo 19; contracts are absorbed into core `hr` as the `hr.version` model (extend `hr.version`, not `hr.contract`; decided 2026-07-07, review D1).
- Salary-rule `amount_python_compute` context: `employee`, `version` (the `hr.version` record — Odoo 19 replaces the v3.0D `contract` variable), `payslip`, `worked_days`, `inputs`, `categories`, `rules`, `env` — must assign `result`. Hidden intermediates carry `appears_on_payslip = False`.
- UI strings and model menus are Dutch (e.g. Salarisadministratie → Configuratie → Tarieven); keep statutory terms in their official form (`basiskorting`, not `basisaftrek`).
- Working-hours divisor is the fixed constant **173.33 hrs/month** (8h × 5d × 52wk ÷ 12).
- Official-localization conformance (added 2026-10-06): before every commit, `tools/check_l10n_conformance.py` (git pre-commit hook, warnings only) compares the module with the conventions in `docs/reference/official-localization-checklist.md`. A new divergence is either fixed or recorded in `docs/reference/official-localization-divergences.md` in the same change; deciding an Open divergence is a PO decision and follows the spec-sync discipline.
- Upgrade watch list (added 2026-10-06): every change that hooks into Odoo (an inherited model, an overridden method, a referenced XML id, a relied-on behaviour) adds an entry to `docs/reference/upgrade-watch-list.md` in the same change. Append new entries; never renumber existing ones, because other docs cite them as `§N.M`.

## Markdown output conventions

When generating Markdown deliverables (e.g. `_bmad-output/planning-artifacts/epics_EN-20261008.md` and other planning/output docs), follow these rules so they convert cleanly to Word via pandoc:

- **No horizontal-rule separators** (`---`, `***`, `___`) in the document body. *Exception:* a leading YAML frontmatter block delimited by `---` is allowed where a tool requires it (e.g. BMad `stepsCompleted` / `inputDocuments`).
- **Headings: at most 3 levels, and the heading structure starts at Heading 1** (`#` → `##` → `###`; never deeper).
- **Title + subtitle** at the top, as pandoc custom-style fenced divs:

  ```
  ::: {custom-style="Title"}
  The Title Text
  :::
  ::: {custom-style="Subtitle"}
  The Sub-Title Text
  :::
  ```

- **Blank line before the first bullet:** after any heading or label that introduces a bulleted list, leave one empty line before the first `-` item.

## Working principles (Karpathy Skills)

Four general coding principles, each anchored to where it bites hardest in *this* repo.

- **Think Before Coding** — State assumptions explicitly; if uncertain, ask. Present multiple interpretations when they exist rather than proceeding on a silent guess. Here this is not optional: the design has an **open blocking question** (is overtime in the premium base?) and a **flagged contradiction** (hardcoded rate literals vs. the dated-rate-authority invariant). Surface these; never quietly pick a side on a statutory question.
- **Simplicity First** — Minimum code that solves the problem; nothing speculative. No unrequested features, abstractions, flexibility, or error handling for impossible cases. Respect the hard scope line: **v1.0R is monthly payroll only** — do not build deferred v1.1R+ items (extra pay periods, ZV sick pay, CSV exports, bank-payment routing, Loonbelastingkaart categories, gevarenklasse model) early. Net deductions including loans and garnishments are v1.0R (decided 2026-10-08).
- **Surgical Changes** — Touch only what you must; clean up only your own mess; match existing style. Don't refactor working code or "improve" unrelated rules. This reinforces the **layer boundaries** and the **never-gate list**: editing a premium rule must not perturb a shared base (`*_PREM_INC`, `TAX_INC`, `LOONBEL_RAW`, `NET_PRE`, `NET_CARRY`, `NET`, `TOTAL_ER_COST`).
- **Goal-Driven Execution** — Define success criteria, then loop until verified. The PRD's **acceptance criteria** are the verification target: calculations reconcile to the official 2026 publications within XCG 0.02, every run close yields a balanced `account.move`, disabling a premium yields `0.00` without disturbing NET, and rates update with no code deploy.
