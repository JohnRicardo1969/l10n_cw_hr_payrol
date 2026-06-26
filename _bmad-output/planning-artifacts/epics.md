---
stepsCompleted: ['step-01-validate-prerequisites']
inputDocuments:
  - 'docs/prd/PRD - v3.0D.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-l10n_cw_hr_payrol-2026-06-25/ARCHITECTURE-SPINE.md'
  - 'docs/tech_design_l10n_cw_hr_payroll_v3.0D.txt'
---

::: {custom-style="Title"}
l10n_cw_hr_payroll — Epic Breakdown
:::
::: {custom-style="Subtitle"}
Curaçao Payroll Localization for Odoo 19 Enterprise — v1.0R
:::

# Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for l10n_cw_hr_payroll, decomposing the requirements from the PRD and Architecture Spine (with the v3.0D Technical Design as implementation reference) into implementable stories. There is no separate UX design contract: the module uses Odoo's native UI, extended only where Odoo models are extended, plus a scoped in-module SCSS theme.

## Requirements Inventory

### Functional Requirements

**Statutory calculation engine**

- FR001: Compute monthly payroll for all employees in a run with a single action.
- FR002: Execute the canonical statutory calculation as ordered `hr.salary.rule` records evaluated in strict ascending Sequence 10–150 (the ~21 rules that map the 14 statutory Steps), with hidden intermediates carrying `appears_on_payslip = False`.
- FR003: Compute `TOTAL_LOON` = contract wage + fringe benefits (natura-loon).
- FR004: Compute four overtime types (weekday, Saturday, Sunday, public holiday) as separate named payslip lines, from hours inputs and per-employee configurable rates, contributing to ALW.
- FR005: Compute BVZ — employer flat 9.3% and employee sliding 0%–4.3% — on the annualised, capped BVZ premium base.
- FR006: Compute AOV/AWW — employee 6.5% and employer 9.5% up to the ceiling, plus a 1% employee surcharge on income above the ceiling.
- FR007: Compute AVBZ — employee sliding 0.5%/1.5% by the low-income threshold and employer flat 0.5% — on the AOV base capped at the AVBZ ceiling.
- FR008: Compute loonbelasting via the progressive bracket table (`compute_tax`), returning raw tax, then apply toeslagen as monetary deductions from the tax amount (not income reductions), floored at zero.
- FR009: Apply basiskorting automatically to all employees; apply alleenverdieners-, kinder-, and ouderentoeslag from per-employee fields.
- FR010: Compute extra tax on bijzondere beloningen using the separate (exclusief basiskorting) marginal-rate table, applied only to the bijzondere beloning amount.
- FR011: Compute ZV (employer 1.9%) and OV (employer variable by gevarenklasse) on the shared ZV/OV wage ceiling, using the contract base wage (excluding fringe benefits).
- FR012: Compute `NET` (= BASIC + ALW + DED) and `NONTAXED` (onbelaste vergoedingen) as a separate post-NET line; amount paid = NET + NONTAXED.
- FR013: Compute `TOTAL_ER_COST` (informational total employer cost aggregate).
- FR014: Enable/disable individual premiums and taxes per employee via the `enabled` flag, returning 0.00 without breaking the calculation chain; shared income-base intermediates always execute.

**Wage component model & configuration**

- FR015: Provide the three-tier wage component model — Tier 1 global rules (`hr.salary.rule`), Tier 2 company-scoped template sets (`hr.wage.component.set` + lines), Tier 3 per-employee wage lines (`hr.employee.wage.line`).
- FR016: Apply a Tier 2 component set to one or more employees via the apply wizard, creating independent Tier 3 records that do not propagate later set edits.
- FR017: Store all statutory rates, ceilings, and thresholds as dated `hr.tax.bracket` records; update rates by setting `valid_to` and inserting new dated records, with no code deployment.
- FR018: Maintain per-employee, per-component, per-year YTD accumulation (`hr.wage.component.ytd`), updated on run close and retained across years.
- FR019: Provide per-employee toeslag fields and beschikking input, and a per-contract OV percentage field.

**Run lifecycle & accounting**

- FR020: Drive the run lifecycle CONCEPT → TE CONTROLEREN → AFGESLOTEN and payslip lifecycle CONCEPT → TE CONTROLEREN → BEVESTIGD (with cancel), allowing recompute (herberekening) before close.
- FR021: On close, confirm and lock payslips, recompute YTD, post the journal entry, and expose run-level reports — as the single state-commit point.
- FR022: Generate a balanced `account.move` on close (total debit ≡ total credit by construction) using the configurable GL mapping.

**Reports**

- FR023: Produce the payslip PDF (A-01) in Curaçao layout.
- FR024: Produce the monthly wage tax declaration (B-01) and SVB premium declaration (B-02) per run.
- FR025: Produce the balanced payroll journal entry summary (B-05) per run.

**Security & access**

- FR026: Provide four security roles (Employee, Payroll User, Payroll Manager, Accountant) enforcing least privilege.
- FR027: Restrict employees to their own payslips via a record rule (`employee_id.user_id = user`).

### NonFunctional Requirements

- NFR001: **Statutory correctness** — calculation output reconciles to the official 2026 Belastingdienst/SVB publications within XCG 0.02 (rounding tolerance), for representative employees (standard, BVZ-exempt, above-ceiling, with bijzondere beloning).
- NFR002: **Auditability** — every calculation step traceable: intermediates materialized as rules, rates inspectable as dated records, `mail.thread` chatter on all custom models, append-only tax bracket records.
- NFR003: **Operational independence** — monthly payroll runs end to end inside Odoo with no external payroll service or spreadsheet.
- NFR004: **Regulatory agility** — annual or ad-hoc rate changes require no code deployment; historical records preserved for accurate recomputation of prior periods.
- NFR005: **Accounting integrity** — every run close produces a balanced journal entry by construction.
- NFR006: **Data protection** — least privilege via group-based access, audit trail, append-only statutory records, no transmission of payroll data to external services (Landsverordening bescherming persoonsgegevens).
- NFR007: **Platform** — Odoo 19 Enterprise on Odoo.sh or self-hosted Enterprise; Odoo SaaS unsupported.
- NFR008: **Idempotent close** — reopening and re-closing a run must not double-count YTD or post duplicate/unbalanced journals (Architecture AD-9).

### Additional Requirements

**From the Architecture Spine (invariants AD-1…AD-15) — these govern every calculation story:**

- AR001: **No starter template.** Greenfield Odoo module; the first epic scaffolds the module per Tech Design §13 (manifest, package layout, layer boundaries AD-11).
- AR002: **Sign convention (AD-1)** — employee deductions/premiums negative; employer costs and bases positive.
- AR003: **Category-assignment contract (AD-2)** — NET = BASIC+ALW+DED (DED negative); ER excluded; overtime in ALW; NONTAXED a separate post-NET line.
- AR004: **Strict sequence + reference discipline (AD-3)** — fixed ascending Sequence; reference only prior results via `rules.CODE.amount` / `categories.X`.
- AR005: **Annualisation convention (AD-4)** — ×12 → apply annual ceiling/scale/bracket → ÷12.
- AR006: **Dated-rate authority (AD-5)** — ALL statutory rates/ceilings (premiums included) live in `hr.tax.bracket`; **no rate literals in rule Python** (overrides the v3.0D hardcoded listings). Requires a **seed change**: expand `tax_type` to granular per-(insurance, payer) values (`bvz_emp`, `bvz_er`, `avbz_emp`, `avbz_er`, `aov_aww_emp`, `aov_aww_er`, `aov_aww_surcharge`, `zv`, `ov`, `loonbelasting`, `bijzondere_beloning`) with a defined read contract per type.
- AR007: **Enable/disable gate + never-gate set (AD-6)** — never gate BVZ_PREM_INC, AOV_PREM_INC, TAX_INC, LOONBEL_RAW, NET, TOTAL_ER_COST.
- AR008: **active vs enabled split (AD-7)** — exemption for audit = `active=True, enabled=False`.
- AR009: **Three-tier decoupling (AD-8)** — apply is a one-time copy; T3.salary_rule_id read-only after creation.
- AR010: **Single state-commit point (AD-9)** — only `action_close()` mutates YTD and the journal; YTD recomputed (not blindly incremented) for idempotent reopen/re-close; reopen reverses the `account.move`.
- AR011: **Balance by construction (AD-10)** — GL numbers indicative, mapped per company at onboarding.
- AR012: **Money & rounding (AD-12)** — XCG; round to 2 dp; `compute_tax` returns raw tax before toeslagen.
- AR013: **Statutory defaults unconditional (AD-13)** — verwervingskosten (41.67/mo) and basiskorting (2 915/yr) auto-applied to all employees for v1.0R.

**Manifest & seed data (Tech Design §13):**

- AR014: Manifest — `depends: [hr, hr_contract, hr_holidays, hr_payroll, hr_payroll_account, hr_attendance]` (no theme dependency added), version `19.0.0.1.0`, country `cw`, license `OPL-1`, `application=False`, `auto_install=False`, plus an `assets` key registering `static/src/scss/cw_theme_prl10n.scss` in `web.assets_backend` (see UX-DR001).
- AR015: Ship seed data — `CWMONTHLY` structure type, `CWSTAFF` structure, salary-rule categories, all CW salary rules, and the 2026 dated rate records (loonbelasting brackets, SVB premiums/ceilings, bijzondere beloningen, toeslagen).
- AR016: Provide Dutch UI translations (`i18n/nl.po`).

**Resolved / deferred open questions:**

- AR017 (**RESOLVED — confirmed by product owner**): AD-14 — overtime **is** included in the premium income base. Confirmed via research (~90% of cases require inclusion; adopted for all). Premium bases derive from `categories.BASIC + categories.ALW`. No longer blocking; AD-14 promoted to `[ADOPTED]` in the spine.
- AR018 (deferred, non-blocking): OQ-01 payslip distribution; OQ-03 confirm overtime default rates (150/150/200/200); OQ-04 granular per-group rights; OQ-05 final GL numbers; OQ-07 SVB gevarenklasse model (interim Float → future Many2one). Out of scope for v1.0R: additional pay periods, ZV sick pay, loans/garnishments, verzamelloonstaat/jaaropgaaf CSV, e-filing, DGA, Aruba/SXM.

### UX Design Requirements

The module uses Odoo's native UI (list/form/menu views), with a custom scoped SCSS theme for the module's own views. Reference (read-only, not a dependency): `/home/nroosje/dev/odoo-sh/odoo-cbw-ent/service-business-suite/cw_theme`.

- UX-DR001: Provide a scoped SCSS theme **`cw_theme_prl10n`** bundled **inside** `l10n_cw_hr_payroll` (`static/src/scss/cw_theme_prl10n.scss`), registered via the manifest **`assets`** key under `web.assets_backend` (not the `data` list). No new module and no new manifest dependency.
- UX-DR002: Scope **all** theme rules under a single `.cw_theme_prl10n` wrapper class, applied **only** to the module's own custom-model views (`hr.tax.bracket`, `hr.wage.component.set`, `hr.employee.wage.line`, and CW-owned payslip/run views/reports). **Never** add the wrapper to inherited Odoo-model views (`hr.employee`, `hr.contract`, `hr.salary.rule` extensions) — Odoo's own pages must render visually unchanged.
- UX-DR003: Define pastel design tokens as CSS variables for **light** (`:root`) and **dark** (`.o_dark_mode`) mode, reusing cw_theme's palette (lavender/violet accent; mint/peach/sky/rose supporting tints). Tokens are **copied** into this module; cw_theme remains reference only, not a runtime dependency.
- UX-DR004 (deferred): Portal-page styling (the cw_theme `.cw-portal` equivalent) is out of scope for v1.0R and revisited with payslip distribution (OQ-01); only backend styling ships in v1.0R.

### FR Coverage Map

{{requirements_coverage_map}}

## Epic List

{{epics_list}}
