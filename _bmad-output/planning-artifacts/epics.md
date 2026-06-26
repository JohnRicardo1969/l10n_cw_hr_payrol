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
Curaçao Payroll Localization for Odoo 19 Enterprise — version 19.0.0.1.0
:::

# Epic Breakdown

## Overview

This document breaks the requirements from the PRD and the Architecture Spine (with the v3.0D Technical Design as the implementation reference) into epics and stories that can be built. There is no separate UX design document: the module uses Odoo's standard screens, extended only where Odoo models are extended, plus a small in-module stylesheet theme.

## Requirements Inventory

### Functional Requirements

**Statutory calculation engine**

- FR001: Compute monthly payroll for all employees in one run with a single action.
- FR002: Run the statutory calculation as an ordered set of Odoo Salary Rule records (`hr.salary.rule`), evaluated in strict ascending order (Sequence 10–150) — the roughly 21 rules that carry out the 14 statutory Steps. Internal helper rules are hidden from the payslip by turning off the "show on payslip" flag (`appears_on_payslip = False`).
- FR003: Compute total gross pay — the gross-pay rule (`TOTAL_LOON`) = monthly contract wage + benefits in kind (natura-loon).
- FR004: Compute four overtime types (weekday, Saturday, Sunday, public holiday) as separate, named payslip lines, from entered hours and a per-employee rate, each added to the allowances category (`ALW`).
- FR005: Compute the BVZ health premium — employer flat 9.3% and employee on a sliding scale 0%–4.3% — on the yearly-capped BVZ base.
- FR006: Compute the AOV/AWW old-age and survivor premium — employee 6.5% and employer 9.5% up to the ceiling — plus a 1% employee surcharge on income above the ceiling.
- FR007: Compute the AVBZ long-term-care premium — employee on a sliding 0.5%/1.5% by the low-income threshold, employer flat 0.5% — on the AOV base capped at the AVBZ ceiling.
- FR008: Compute wage tax (loonbelasting) through the tax-calculation method (`compute_tax`) using the progressive bracket table, which returns the raw tax; then subtract the tax credits (toeslagen) as money off the tax amount (not off taxable income), with a floor of zero.
- FR009: Apply the standard tax credit (basiskorting) automatically to every employee; apply the single-earner, child, and elderly credits (alleenverdieners-, kinder-, ouderentoeslag) from fields on the employee.
- FR010: Compute the extra tax on special remuneration (bijzondere beloningen) using its own marginal-rate table (the "exclusief basiskorting" variant), applied only to the special-remuneration amount.
- FR011: Compute the ZV sickness premium (employer 1.9%) and the OV accident premium (employer, variable by risk class / gevarenklasse) on the shared ZV/OV wage ceiling, using the base contract wage (excluding benefits in kind).
- FR012: Compute net pay — the net-pay rule (`NET`) = basic + allowances + deductions categories (`BASIC + ALW + DED`) — and untaxed reimbursements (onbelaste vergoedingen) as a separate line after net through the untaxed rule (`NONTAXED`); the amount paid out = net + untaxed.
- FR013: Compute total employer cost as an informational total through the employer-cost rule (`TOTAL_ER_COST`).
- FR014: Let the payroll admin switch individual premiums and taxes on or off per employee through the enable flag (`enabled`) on the employee's wage line; a disabled rule returns 0.00 without breaking the chain, while the shared base rules always run.

**Wage component model and configuration**

- FR015: Provide the three-tier wage-component model — Tier 1 global rules (the Salary Rule model, `hr.salary.rule`), Tier 2 company template sets (the Wage Component Set model, `hr.wage.component.set`, with its lines), and Tier 3 per-employee wage lines (the Employee Wage Line model, `hr.employee.wage.line`).
- FR016: Apply a Tier 2 template set to one or more employees through the apply wizard, creating independent Tier 3 wage lines that do not change when the set is edited later.
- FR017: Store every statutory rate, ceiling, and threshold as dated records in the Tax Bracket model (`hr.tax.bracket`); change a rate by closing the old record (set its valid-until date, `valid_to`) and adding a new dated record — with no code deployment.
- FR018: Keep a running year-to-date total per employee, per component, per year in the Year-to-Date model (`hr.wage.component.ytd`), updated when a run is closed and kept across years.
- FR019: Provide the tax-credit fields and the tax-ruling input (beschikking) on the employee, and a risk-class percentage (OV%) on the contract.

**Run lifecycle and accounting**

- FR020: Drive the run through its stages (Draft → To Check → Closed / CONCEPT → TE CONTROLEREN → AFGESLOTEN) and each payslip through its stages (Draft → To Check → Confirmed / CONCEPT → TE CONTROLEREN → BEVESTIGD, with cancel), allowing recalculation (herberekening) before close.
- FR021: On close, confirm and lock the payslips, recompute the year-to-date totals, post the journal entry, and make the run reports available — this close is the one and only point where results are committed.
- FR022: On close, generate a balanced journal entry (the accounting move, `account.move`) where total debit equals total credit by construction, using the configurable general-ledger mapping.

**Reports**

- FR023: Produce the payslip PDF (report A-01) in Curaçao layout.
- FR024: Produce the monthly wage-tax return (report B-01) and the SVB premium return (report B-02) per run.
- FR025: Produce the balanced payroll journal-entry summary (report B-05) per run.

**Security and access**

- FR026: Provide four security roles (Employee, Payroll User, Payroll Manager, Accountant) with least-privilege access.
- FR027: Limit each employee to their own payslips with a record rule that matches the logged-in user (`employee_id.user_id = user`).

**Run membership and contract period**

- FR028: A payroll run **automatically** leaves an employee out for a period when (a) they have no worked hours in that period, or (b) they are no longer in service (their contract ended on or before the period). This is automatic — never a manual step; left-out employees get no payslip and do not appear in the run totals or the journal entry.
- FR029: Each employment contract has a required start date and an optional end date; entering an end date sets when the employee leaves service. The run uses these dates to decide whether an employee is in service for the period (see FR028). Permanent contracts with no end date are allowed.

### NonFunctional Requirements

- NFR001: **Statutory correctness** — output matches the official 2026 Belastingdienst/SVB publications within XCG 0.02 (rounding only), for representative employees (standard, BVZ-exempt, above the ceiling, and with special remuneration).
- NFR002: **Auditability** — every step is traceable: helper amounts exist as their own rules, rates are inspectable dated records, every custom model has a change log (the messaging/chatter mixin, `mail.thread`), and rate records are append-only.
- NFR003: **Operational independence** — the full monthly payroll runs inside Odoo, with no external payroll service or spreadsheet.
- NFR004: **Regulatory agility** — yearly or ad-hoc rate changes need no code deployment; old records stay so past periods recompute correctly.
- NFR005: **Accounting integrity** — every close produces a balanced journal entry by construction.
- NFR006: **Data protection** — least-privilege group access, an audit trail, append-only statutory records, and no sending of payroll data to outside services (Landsverordening bescherming persoonsgegevens).
- NFR007: **Platform** — Odoo 19 Enterprise on Odoo.sh or self-hosted Enterprise; Odoo SaaS is not supported.
- NFR008: **Idempotent close** — reopening and re-closing a run must not double-count the year-to-date totals or post duplicate or unbalanced journal entries (Architecture AD-9).

### Additional Requirements

**From the Architecture Spine (invariants AD-1…AD-15) — these govern every calculation story:**

- AR001: **No starter template.** This is a fresh (greenfield) Odoo module; the first epic sets up the module skeleton per Tech Design §13 (manifest, package layout, and the layer boundaries, AD-11).
- AR002: **Sign convention (AD-1)** — employee deductions and premiums are negative; employer costs and base amounts are positive.
- AR003: **Category rules (AD-2)** — net = basic + allowances + deductions (`BASIC + ALW + DED`, with deductions negative); employer costs sit in the employer category (`ER`) and are left out of net; overtime goes in allowances (`ALW`); untaxed reimbursements (`NONTAXED`) are a separate line after net.
- AR004: **Strict order and reference discipline (AD-3)** — fixed ascending order; a rule may read only earlier results — prior rule amounts (`rules.CODE.amount`) and category totals (`categories.X`).
- AR005: **Annualisation (AD-4)** — multiply the monthly base by 12, apply the yearly ceiling/scale/bracket, then divide back by 12.
- AR006: **Rates are data (AD-5)** — every statutory rate and ceiling (premiums included) lives in the Tax Bracket model (`hr.tax.bracket`); no rate values are hard-coded in rule Python (this overrides the hard-coded v3.0D listings). It needs a seed change: split the rate-type field (`tax_type`) into specific values per insurance and payer (`bvz_emp`, `bvz_er`, `avbz_emp`, `avbz_er`, `aov_aww_emp`, `aov_aww_er`, `aov_aww_surcharge`, `zv`, `ov`, `loonbelasting`, `bijzondere_beloning`), each with a defined way to read it.
- AR007: **Enable/disable gate and never-gate set (AD-6)** — never disable the shared base rules: the BVZ base (`BVZ_PREM_INC`), the AOV base (`AOV_PREM_INC`), the tax base (`TAX_INC`), the raw tax (`LOONBEL_RAW`), net (`NET`), and employer cost (`TOTAL_ER_COST`).
- AR008: **Visible vs. counted in the calculation (AD-7)** — an audit exemption keeps the line visible but out of the calculation (visibility flag on, calculation flag off: `active=True, enabled=False`).
- AR009: **Three-tier decoupling (AD-8)** — applying a set is a one-time copy; the linked rule on a Tier 3 wage line (`salary_rule_id`) is read-only after creation.
- AR010: **One commit point (AD-9)** — only the run-close action (`action_close()`) changes the year-to-date totals and the journal; the totals are recomputed (not blindly added to) so reopening and re-closing stays correct, and reopening reverses the journal entry (`account.move`).
- AR011: **Balanced by construction (AD-10)** — the general-ledger account numbers are indicative, mapped per company at onboarding.
- AR012: **Money and rounding (AD-12)** — currency XCG; round to 2 decimals; the tax-calculation method (`compute_tax`) returns the raw tax before tax credits (toeslagen).
- AR013: **Standard credits always apply (AD-13)** — the acquisition-cost allowance (verwervingskosten, 41.67/month) and the standard tax credit (basiskorting, 2 915/year) apply automatically to every employee in v1.0R.

**Manifest and seed data (Tech Design §13):**

- AR014: **Manifest** — depends on (`hr, hr_contract, hr_holidays, hr_payroll, hr_payroll_account, hr_attendance`) with no theme dependency added; version `19.0.0.1.0`; country `cw`; license `OPL-1`; not an app and not auto-installed (`application=False, auto_install=False`); plus an assets entry (`assets`) that loads the theme stylesheet (`static/src/scss/cw_theme_prl10n.scss`) into the backend bundle (`web.assets_backend`) — see UX-DR001.
- AR015: **Seed data** — ship the monthly structure type (`CWMONTHLY`), the standard-staff structure (`CWSTAFF`), the salary-rule categories, all CW salary rules, and the 2026 dated rate records (loonbelasting brackets, SVB premiums and ceilings, special-remuneration rates, tax credits).
- AR016: **Translations** — provide the Dutch interface translation file (`i18n/nl.po`).

**Resolved / deferred open questions:**

- AR017 (**RESOLVED — confirmed by product owner**): AD-14 — overtime **is** included in the premium base. Confirmed by research (~90% of cases require it; adopted for all). Premium bases come from the basic and allowance categories (`categories.BASIC + categories.ALW`). No longer blocking; AD-14 is now adopted in the spine.
- AR018 (deferred, non-blocking): OQ-01 payslip distribution; OQ-03 confirm the overtime default rates (150/150/200/200); OQ-04 fine-grained rights per role; OQ-05 final general-ledger account numbers; OQ-07 the SVB risk-class model (interim plain number field → future dropdown link, Many2one). Out of scope for v1.0R: hourly gross from worked hours (v1.0R uses the fixed monthly wage; employees with no worked hours are left out automatically, FR028); extra pay periods, ZV sick pay, loans/garnishments, the annual collective wage statement / wage-tax card CSV (verzamelloonstaat / jaaropgaaf), electronic filing, DGA payroll, and Aruba/Sint Maarten.

### UX Design Requirements

The module uses Odoo's standard screens (list/form/menu views), with a custom scoped stylesheet theme for the module's own screens. Reference (read-only, not a dependency): `/home/nroosje/dev/odoo-sh/odoo-cbw-ent/service-business-suite/cw_theme`.

- UX-DR001: Provide a scoped stylesheet theme named `cw_theme_prl10n`, bundled **inside** the module as a stylesheet file (`static/src/scss/cw_theme_prl10n.scss`) and loaded through the manifest assets entry (`assets`) into the backend bundle (`web.assets_backend`) — not the data list. No new module and no new dependency.
- UX-DR002: Put **every** theme rule under one wrapper CSS class (`.cw_theme_prl10n`), applied **only** to the module's own model screens (the Tax Bracket, Wage Component Set, and Employee Wage Line views, and CW-owned payslip/run views and reports). **Never** add the wrapper to extended Odoo views (Employee, Contract, Salary Rule) — Odoo's own pages must look unchanged.
- UX-DR003: Define the pastel colours as CSS variables for light mode (the page root, `:root`) and dark mode (Odoo's dark-mode class, `.o_dark_mode`), reusing cw_theme's palette (lavender/violet accent; mint/peach/sky/rose support tints). The colours are copied into this module; cw_theme stays a reference only, not a dependency.
- UX-DR004 (deferred): Portal-page styling (the portal counterpart in cw_theme, `.cw-portal`) is out of scope for v1.0R and revisited with payslip distribution (OQ-01); only backend styling ships in v1.0R.

### FR Coverage Map

{{requirements_coverage_map}}

## Epic List

{{epics_list}}

# Definitions

## Abbreviations

- AOV — Algemene Ouderdomsverzekering (general old-age insurance).
- AWW — Algemene Weduwen- en Wezenverzekering (general widows' and orphans' insurance).
- AVBZ — Algemene Verzekering Bijzondere Ziektekosten (long-term-care insurance).
- BVZ — Basisverzekering Ziektekosten (basic health insurance).
- ZV — Ziekteverzekering (sickness insurance; employer-only).
- OV — Ongevallenverzekering (accident insurance; employer-only, by risk class).
- SVB — Sociale Verzekeringsbank (social insurance bank).
- DGA — Directeur-grootaandeelhouder (director / major shareholder).
- XCG — Curaçao guilder (the module's currency).
- GL — General Ledger.
- YTD — Year-to-Date.
- PRD — Product Requirements Document.
- AD — Architecture Decision (a numbered invariant in the Architecture Spine).
- FR / NFR — Functional / Non-Functional Requirement.
- AR — Additional Requirement (architecture-driven).
- UX-DR — UX Design Requirement.
- OQ — Open Question.
- UI / UX — User Interface / User Experience.
- SCSS / CSS — stylesheet languages (Sassy CSS / Cascading Style Sheets).
- PDF / CSV — document / comma-separated-values file formats.
- Tier 1/2/3 — the three layers of the wage-component model (global rules / template sets / employee wage lines).
- v1.0R — the first production release (manifest version 19.0.1.0.0).

## Statutory and domain terms

- loonbelasting — wage tax.
- basiskorting — standard tax credit applied to every employee.
- toeslagen — tax credits subtracted from the computed tax (alleenverdieners-, kinder-, ouderentoeslag = single-earner, child, elderly credits).
- bijzondere beloningen — special (non-periodic) remuneration, taxed on its own table.
- verwervingskosten — fixed acquisition-cost allowance.
- gevarenklasse — SVB risk class that sets the OV percentage.
- natura-loon / loon in natura — benefits in kind.
- beschikking — individual tax ruling from the Belastingdienst.
- onbelaste vergoedingen — untaxed reimbursements.
- herberekening — recalculation of a run before close.
- verzamelloonstaat / jaaropgaaf — annual collective wage statement / annual wage-tax card (both deferred).
- Belastingdienst — the Curaçao tax authority.
- Landsverordening bescherming persoonsgegevens — Curaçao data-protection ordinance.
- Run/payslip stages — CONCEPT (draft), TE CONTROLEREN (to check), AFGESLOTEN (run closed), BEVESTIGD (payslip confirmed).

## Models and technical identifiers

- `hr.salary.rule` — Salary Rule model (one calculation step).
- `hr.wage.component.set` — Wage Component Set model (Tier 2 template).
- `hr.employee.wage.line` — Employee Wage Line model (Tier 3, per employee).
- `hr.tax.bracket` — Tax Bracket model (dated statutory rates).
- `hr.wage.component.ytd` — Year-to-Date totals model.
- `account.move` — Odoo journal entry.
- `mail.thread` — Odoo mixin providing the change log (chatter).
- Salary-rule codes — `TOTAL_LOON` (gross pay), `NET` (net pay), `NONTAXED` (untaxed reimbursements), `TOTAL_ER_COST` (employer cost), and the hidden bases `BVZ_PREM_INC`, `AOV_PREM_INC`, `TAX_INC`, `LOONBEL_RAW`.
- Categories — `BASIC` (basic pay), `ALW` (allowances), `DED` (deductions), `ER` (employer cost).
- Fields and flags — `appears_on_payslip` (show on payslip), `enabled` (counts in the calculation), `active` (visible), `valid_from` / `valid_to` (rate validity dates), `salary_rule_id` (linked rule), `tax_type` (rate type), `employee_id.user_id` (owner link used by the record rule).
- `tax_type` values — `loonbelasting`, `bijzondere_beloning`, `bvz_emp`, `bvz_er`, `avbz_emp`, `avbz_er`, `aov_aww_emp`, `aov_aww_er`, `aov_aww_surcharge`, `zv`, `ov`.
- `compute_tax` — method returning the raw tax from the bracket table.
- `action_close()` — the run-close action; the single commit point.
- `CWMONTHLY` / `CWSTAFF` — the monthly structure type / standard-staff salary structure.
- Manifest keys — `depends`, `version`, `country`, `license`, `application`, `auto_install`, `assets`, `data`.
- `web.assets_backend` — Odoo backend asset bundle.
- `.cw_theme_prl10n` — theme wrapper CSS class; `:root` / `.o_dark_mode` — light / dark mode token scopes; `.cw-portal` — portal scope (deferred).
- `static/src/scss/cw_theme_prl10n.scss` — the theme stylesheet; `i18n/nl.po` — the Dutch translation file.
