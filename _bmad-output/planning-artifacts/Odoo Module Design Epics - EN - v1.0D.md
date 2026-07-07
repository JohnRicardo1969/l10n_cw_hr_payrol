---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
inputDocuments:
  - 'docs/prd/PRD - v3.0D.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-l10n_cw_hr_payrol-2026-06-25/ARCHITECTURE-SPINE.md'
  - 'docs/tech_design_l10n_cw_hr_payroll_v3.0D.txt'
  - 'docs/design/cw-vacation-accrual-v1.1R.md'
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
- FR005: Compute the BVZ health premium — employer flat 9.3% and employee flat 4.3% (per the official SVB 2026 table; there is no income-graduated employee scale) — on the yearly-capped BVZ base (XCG 150,000/year).
- FR006: Compute the AOV/AWW old-age and survivor premium — employee 6.5% and employer 9.5% up to the XCG 100,000/year ceiling, applied **cumulatively** (AD-24) — plus a 1% employee surcharge on year-to-date income above the ceiling.
- FR007: Compute the AVBZ long-term-care premium — employee flat 1.5%, employer flat 0.5% (per the official SVB 2026 table; there is no income-graduated employee scale) — on the AOV base capped at the AVBZ ceiling (XCG 606,247.08/year).
- FR008: Compute wage tax (loonbelasting) by looking up the gross periodic tax in the official Belastingdienst loonbelasting table (`hr.loonbelasting.tabel`) for the fiscal wage base (`TAX_INC`) and the payslip period-end date. For wages above the table ceiling, add the table's above-ceiling rate (46.5% for 2026) on the excess (Ministerial Regulation 144, § Algemeen). The raw table result is the `LOONBEL_RAW` amount (Seq 90); the monthly loonbelasting accumulates in the year-to-date model for the loonbelastingkaart and verzamelloonstaat. Then subtract the tax credits (toeslagen: basiskorting plus any employee-specific credits) as a monetary deduction from that raw tax amount — not from taxable income — with a floor of zero (Seq 100, `LOONBEL`). The 2026 maandtabel is published **exclusief basiskorting** (it taxes from the first gulden), so the basiskorting is subtracted separately here — it is **not** already in the table. Example: TAX_INC = XCG 3,245.00/month → look up wage_from = 3,245 in the 2026 maandtabel → loonbelasting = XCG 316.39 raw; basiskorting = XCG 2,915.00/12 = XCG 242.92; LOONBEL = −(316.39 − 242.92) = −XCG 73.47. Above-ceiling example: wage = XCG 20,000.00/month → ceiling tax XCG 4,862.91 (at the 16,670 ceiling) + 46.5% × (20,000 − 16,670 = 3,330) = XCG 1,548.45 → loonbelasting = XCG 6,411.36.
- FR009: Apply the standard tax credit (basiskorting) automatically to every employee; apply the single-earner, child, and elderly credits (alleenverdieners-, kinder-, ouderentoeslag) from fields on the employee.
- FR010: Compute the extra tax on special remuneration (bijzondere beloningen — vakantiegeld, bonus, gratificatie, incidentele overuren) via the bijzondere-beloningen marginal-rate table ("exclusief basiskorting"): look up the single band rate for the employee's jaarloon (`lookup_marginal_rate`) and apply it to the special-remuneration amount only. The rate (tarief) is fixed **once per tax year** from the prior-year jaarloon (annualised if partial; the current-year expected jaarloon for new hires), with a payroll-manager **override** to the current-year jaarloon when the prior year is unrepresentative; it is stored per (employee, year) as the carry-forward default and the **applied rate is recorded on the payslip line** (the audit truth). A bijzondere beloning is an `ALW` earning carrying an `is_bijzondere_beloning` flag: it stays in NET and in the SVB premium base (premiums **do** apply), but the `TAX_INC` rule excludes it from the maandtabel so it is taxed by this table only. Overtime has **three** routes — *regulier* (maandtabel), *incidenteel* (this bijzondere table), or *Lei di Bion-vrijgesteld* (exempt — see FR011b/AD-23) — chosen manually by the payroll manager; no frequency threshold in the engine. See AD-21.
- FR011: Compute the ZV sickness premium (employer 1.9%) and the OV accident premium (employer, variable by risk class / gevarenklasse) on the shared ZV/OV **monthly** wage cap (XCG 7,146.10/month), applied directly — not annualised.
- FR011b: Support **Lei di Bion exempt overtime** (AD-23) — overtime up to 10 hours/week, under an approved employer beschikking, is paid free of **both** loonbelasting and SVB premiums (0% / 0%): it carries an `is_lei_di_bion_exempt` flag, is excluded from both `TAX_INC` and the premium bases, yet is still paid in net. The beschikking must be **provided and approved by the Payroll Manager** (`group_l10n_cw_payroll_manager`); without approval, or for hours beyond the cap, the overtime falls back to a taxable route (regulier → maandtabel or incidenteel → bijzondere). Example: 10 overuren = XCG 302.90 gross → exempt: 302.90 net; not exempt (bijzondere 9.75%): 273.37 net.
- FR012: Compute net pay — the net-pay rule (`NET`) = basic + allowances + deductions categories (`BASIC + ALW + DED`) — and untaxed reimbursements (onbelaste vergoedingen) as a separate line after net through the untaxed rule (`NONTAXED`); the amount paid out = net + untaxed.
- FR013: Compute total employer cost as an informational total through the employer-cost rule (`TOTAL_ER_COST`).
- FR014: Let the payroll admin switch individual premiums and taxes on or off per employee through the enable flag (`enabled`) on the employee's wage line; a disabled rule returns 0.00 without breaking the chain, while the shared base rules always run.

**Wage component model and configuration**

- FR015: Provide the three-tier wage-component model — Tier 1 global rules (the Salary Rule model, `hr.salary.rule`), Tier 2 company template sets (the Wage Component Set model, `hr.wage.component.set`, with its lines), and Tier 3 per-employee wage lines (the Employee Wage Line model, `hr.employee.wage.line`).
- FR016: Apply a Tier 2 template set to one or more employees through the apply wizard, creating independent Tier 3 wage lines that do not change when the set is edited later.
- FR017: Store every statutory rate, ceiling, and threshold as dated data so a rate change is a data edit with no code deployment. There are three stores (AD-5): **SVB premiums + ceilings** in a single per-year record (`hr.svb.parameters`, one per year, mirroring the annual SVB table — see AD-22); the **bijzondere beloningen marginal rates and the Belastingdienst scalars** (basiskorting, verwervingskosten, toeslagen) as dated `hr.tax.bracket` records; and **loonbelasting** in the official lb-*tabel (`hr.loonbelasting.tabel` — see FR031 and AD-20). Supersede a value by closing the old record (`valid_to`) and adding a new dated one; all records are append-only.
- FR031: Allow a Payroll Manager to upload a Belastingdienst lb-maandtabel by importing a CSV file into `hr.loonbelasting.tabel` / `hr.loonbelasting.tabel.lijn` via the standard Odoo import action. This covers two scenarios: (a) **Annual upload** — before the first run of each new year, upload the new year's table; if not yet available, the prior year's table (valid-to still open) is used until the new one arrives. (b) **Mid-year correction** — when the Belastingdienst publishes a corrected table for the current year, upload it as a new header record for the same year. The system automatically selects the correct version for each payslip: the active table with `valid_from ≤ payslip.date_to`, ordered by latest `valid_from` first and by upload order if `valid_from` is tied (e.g. a retroactive correction). Herberekening on prior-period payslips picks up the corrected table automatically. Superseded table records are retained for audit.
- FR018: Keep a running year-to-date total per employee, per component, per year in the Year-to-Date model (`hr.wage.component.ytd`), updated when a run is closed and kept across years.
- FR019: Provide the tax-credit fields and the tax-ruling input (beschikking) on the employee, and a risk-class percentage (OV%) on the contract.

**Run lifecycle and accounting**

- FR020: Drive the run through its stages (Draft → To Check → Closed / CONCEPT → TE CONTROLEREN → AFGESLOTEN) and each payslip through its stages (Draft → To Check → Confirmed / CONCEPT → TE CONTROLEREN → BEVESTIGD, with cancel), allowing recalculation (herberekening) before close.
- FR021: On close, confirm and lock the payslips, recompute the year-to-date totals, post the journal entry, and make the run reports available — this close is the one and only point where results are committed.
- FR022: On close, generate a balanced journal entry (the accounting move, `account.move`) where total debit equals total credit by construction, using the configurable general-ledger mapping and the actual calculated amounts (2 decimals).

**Reports**

- FR023: Produce the payslip PDF (report A-01) in Curaçao layout.
- FR024: Produce the monthly wage-tax return (report B-01) and the SVB premium return (report B-02) per run, with amounts shown in whole XCG — decimals are dropped (truncated), not rounded.
- FR025: Produce the balanced payroll journal-entry summary (report B-05) per run.

**Security and access**

- FR026: Provide four security roles (Employee, Payroll User, Payroll Manager, Accountant) with least-privilege access.
- FR027: Limit each employee to their own payslips with a record rule that matches the logged-in user (`employee_id.user_id = user`).

**Run membership and contract period**

- FR028: A payroll run **automatically** leaves an employee out for a period when (a) they have no worked hours in that period, or (b) they are no longer in service (their contract ended on or before the period). This is automatic — never a manual step; left-out employees get no payslip and do not appear in the run totals or the journal entry.
- FR029: Each employment contract has a required start date and an optional end date; entering an end date sets when the employee leaves service. The run uses these dates to decide whether an employee is in service for the period (see FR028). Permanent contracts with no end date are allowed.

**Payslip distribution**

- FR030: Distribute payslips to employees as a separate, explicit action restricted to the most senior existing role, the Payroll Manager (`group_l10n_cw_payroll_manager`), allowed only after run close and an explicit "no restore needed" confirmation. Closing a run does not distribute. The send channel (email / Employee Portal / app) is deferred (OQ-01).

### Vacation accrual (v1.1R)

- FR032: Provide a Curaçao statutory vacation leave type (`hr.leave.type`) and seed the CW public-holiday calendar as `resource.calendar.leaves`, so public holidays are separate paid free days and never deducted from vacation balance.
- FR033: Compute the annual statutory vacation entitlement as `min(workdays_per_week, 5) × 3` days, reading the contracted days per week from the employee's `resource.calendar` (not hours/FTE).
- FR034: Grant the yearly vacation allocation on 1 January and prorate it for mid-year starts, using the basis resolved by OQ-11.
- FR035: Enforce the carryover cap at `6 × workdays_per_week`, lapse excess days, and superannuate prior-year rights after long absence (sickness ≥ 6 months or legal obligations ≥ 6 weeks). The take-window (3 vs 6 months) is resolved by OQ-12.
- FR036: Payout unused statutory vacation days on termination at the statutory day-wage (`monthly_wage × 3 / 65` for 5-day week, `× 3 / 78` for 6-day week), rounding part-days up.

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

**From the Architecture Spine (invariants AD-1…AD-20) — these govern every calculation story:**

- AR001: **No starter template.** This is a fresh (greenfield) Odoo module; the first epic sets up the module skeleton per Tech Design §13 (manifest, package layout, and the layer boundaries, AD-11).
- AR002: **Sign convention (AD-1)** — employee deductions and premiums are negative; employer costs and base amounts are positive.
- AR003: **Category rules (AD-2)** — net = basic + allowances + deductions (`BASIC + ALW + DED`, with deductions negative); employer costs sit in the employer category (`ER`) and are left out of net; overtime goes in allowances (`ALW`); untaxed reimbursements (`NONTAXED`) are a separate line after net.
- AR004: **Strict order and reference discipline (AD-3)** — fixed ascending order; a rule may read only earlier results — prior rule amounts (`rules.CODE.amount`) and category totals (`categories.X`).
- AR005: **Premium ceilings (AD-4 / AD-24)** — SVB premiums with an **annual** ceiling (AOV/AWW, BVZ, AVBZ) are computed **cumulatively** (AD-24): premium on the year-to-date premie-loon capped at the annual ceiling, minus premium already withheld — so a once-yearly lump is charged only on the remaining headroom under the annual maximum (per-month ×12 annualisation is **not** used for these, as it mis-fires at the ceiling). ZV/OV use a monthly cap, applied directly. Loonbelasting uses the period-specific lb-*tabel directly — no annualization (see AR024). Below any ceiling the cumulative result equals flat-rate × base, so ordinary payslips are unchanged.
- AR006: **Rates are data (AD-5)** — no rate, ceiling, or threshold is hard-coded in rule Python (this overrides the hard-coded v3.0D listings). Statutory data lives in three append-only dated stores: **SVB premiums + ceilings** in one per-year `hr.svb.parameters` record (AD-22); **`bijzondere_beloning` rates + the Belastingdienst scalars** (basiskorting, verwervingskosten, toeslagen) in `hr.tax.bracket` keyed by `tax_type`; **loonbelasting** in `hr.loonbelasting.tabel` (AR024). SVB premiums are **not** in `hr.tax.bracket` — moving them to one per-year record keeps each shared ceiling stored exactly once (no per-payer duplicate copies to drift).
- AR007: **Enable/disable gate and never-gate set (AD-6)** — never disable the shared base rules: the BVZ base (`BVZ_PREM_INC`), the AOV base (`AOV_PREM_INC`), the tax base (`TAX_INC`), the raw tax (`LOONBEL_RAW`), net (`NET`), and employer cost (`TOTAL_ER_COST`).
- AR008: **Visible vs. counted in the calculation (AD-7)** — an audit exemption keeps the line visible but out of the calculation (visibility flag on, calculation flag off: `active=True, enabled=False`).
- AR009: **Three-tier decoupling (AD-8)** — applying a set is a one-time copy; the linked rule on a Tier 3 wage line (`salary_rule_id`) is read-only after creation.
- AR010: **One commit point (AD-9)** — only the run-close action (`action_close()`) changes the year-to-date totals and the journal; the totals are recomputed (not blindly added to) so reopening and re-closing stays correct, and reopening reverses the journal entry (`account.move`). The controlled reopen is the only in-app reopen; a whole-database restore is disaster-only and outside the module (a pre-close manual Odoo.sh backup is the operational safety step before close).
- AR011: **Balanced by construction (AD-10)** — the general-ledger account numbers are indicative, mapped per company at onboarding.
- AR012: **Money and rounding (AD-12)** — currency XCG; round to 2 decimals; `lookup_loonbelasting` returns the raw loonbelasting before toeslagen; SVB premium rules read rate/ceiling fields off the per-year `hr.svb.parameters` record; `lookup_marginal_rate` returns the bijzondere-beloningen band rate; `compute_tax` returns the dated Belastingdienst scalars (basiskorting, verwervingskosten, toeslagen). Tax returns show whole XCG (decimals dropped), while payslips and the journal keep the actual 2-decimal amounts.
- AR013: **Standard credits always apply (AD-13)** — the acquisition-cost allowance (verwervingskosten, 41.67/month, a pre-table income deduction at `TAX_INC`/Seq 80; statutory forfeit, max 500/year) and the standard tax credit (basiskorting, 2,915/year = 242.92/month per the official 2026 Belastingdienst *Loonbelastingverklaring 2026*, a post-table tax credit at Seq 100) apply automatically to every employee in v1.0R. (The 3,247.35 figure was an inkomstenbelasting amount, not the loonbelasting withholding basiskorting.)
- AR019: **Senior-only distribution gate (AD-16)** — payslip distribution is a separate action restricted to the most senior existing role, the Payroll Manager group (`group_l10n_cw_payroll_manager`); no new group is added; allowed only after close plus a "no restore needed" confirmation; the send channel is deferred (OQ-01).
- AR020: **Canonical effective date (AD-17)** — every dated-rate lookup, `compute_tax`, and `lookup_loonbelasting` use the payslip period-end date (`payslip.date_to`), never `today()`; so a historical recompute reproduces that period's rates and table.
- AR021: **Fail loud on missing statutory data (AD-18)** — a required statutory rate or loonbelasting table entry missing for the effective date raises a blocking error (`UserError`), never a silent 0 (unlike a deliberately disabled premium).
- AR022: **Company scoping (AD-19)** — national statutory data (the Tax Bracket model, the loonbelasting table model, salary rules, categories, structures) is global; operational data (wage sets/lines, year-to-date, payslips/runs, journal) is company-scoped via `company_id`. Multi-company enablement is an open question.
- AR023: **Schema-migration discipline** — schema changes (e.g. the `tax_type` expansion in AR006) ship migration scripts that preserve historical payslips and closed year-to-date; never destructively drop historical statutory records.
- AR024: **Loonbelasting table model (AD-20)** — loonbelasting is looked up from `hr.loonbelasting.tabel` (header) / `hr.loonbelasting.tabel.lijn` (rows); one row per `(tabel_id, wage_from)`. Header fields: `name`, `period_type`, `year` (Integer), `valid_from`, `valid_to` (nullable), `active`. **Selection rule:** among all `active=True` headers where `period_type` matches, `year = date.year`, and `valid_from ≤ date_to`, pick the one with the latest `valid_from`; ties broken by highest `id` (most recently uploaded). This handles both annual uploads and mid-year corrections without requiring the old table to be archived first. Lookup key = `floor(TAX_INC / step) * step` (maandtabel step = XCG 5.00). Above table ceiling (XCG 16,670/month for 2026): `ceiling_tax + (TAX_INC − ceiling) × 46.5%` (MR 144). Missing table raises `UserError` (AD-18). No annualization — the table is period-specific (AD-4 exception). Effective date = `payslip.date_to` (AD-17). Global scope, no `company_id` (AD-19). Rows are never deleted; superseded headers kept for audit.

**Manifest and seed data (Tech Design §13):**

- AR014: **Manifest** — depends on (`hr, hr_contract, hr_holidays, hr_payroll, hr_payroll_account, hr_attendance`) with no theme dependency added; version `19.0.0.1.0`; country `cw`; license `OPL-1`; not an app and not auto-installed (`application=False, auto_install=False`); plus an assets entry (`assets`) that loads the theme stylesheet (`static/src/scss/cw_theme_prl10n.scss`) into the backend bundle (`web.assets_backend`) — see UX-DR001.
- AR015: **Seed data** — ship the monthly structure type (`CWMONTHLY`), the standard-staff structure (`CWSTAFF`), the salary-rule categories, all CW salary rules, the **2026 `hr.svb.parameters` record** (one per year: all SVB premium rates, the AOV surcharge, and the ceilings), the bijzondere beloningen rate records (6 correct bands per the authoritative 2026 PDF), the Belastingdienst scalars (basiskorting 2,915/yr, verwervingskosten 500/yr, toeslagen), and the 2026 lb-maandtabel entries (≈ 3,335 rows, `period_type = maand`, `valid_from = 2026-01-01`) via CSV seed files.
- AR016: **Translations** — provide the Dutch interface translation file (`i18n/nl.po`).

**Resolved / deferred open questions:**

- AR017 (**RESOLVED — confirmed by product owner**): AD-14 — overtime **is** included in the premium base. Confirmed by research (~90% of cases require it; adopted for all). Premium bases come from the basic and allowance categories (`categories.BASIC + categories.ALW`). No longer blocking; AD-14 is now adopted in the spine.
- AR018 (deferred, non-blocking): OQ-01 payslip distribution; OQ-03 confirm the overtime default rates (150/150/200/200); OQ-04 fine-grained rights per role; OQ-05 final general-ledger account numbers; OQ-07 the SVB risk-class model (interim plain number field → future dropdown link, Many2one). Out of scope for v1.0R: a custom application-level payroll snapshot/restore (v1.1R+; v1.0R relies on the controlled reopen (AD-9), the draft batch as checkpoint, a pre-close manual Odoo.sh backup, and Odoo.sh Staging for testing); hourly gross from worked hours (v1.0R uses the fixed monthly wage; employees with no worked hours are left out automatically, FR028); extra pay periods, ZV sick pay, loans/garnishments, the annual collective wage statement / wage-tax card CSV (verzamelloonstaat / jaaropgaaf), electronic filing, DGA payroll, and Aruba/Sint Maarten.

### UX Design Requirements

The module uses Odoo's standard screens (list/form/menu views), with a custom scoped stylesheet theme for the module's own screens. Reference (read-only, not a dependency): `/home/nroosje/dev/odoo-sh/odoo-cbw-ent/service-business-suite/cw_theme`.

- UX-DR001: Provide a scoped stylesheet theme named `cw_theme_prl10n`, bundled **inside** the module as a stylesheet file (`static/src/scss/cw_theme_prl10n.scss`) and loaded through the manifest assets entry (`assets`) into the backend bundle (`web.assets_backend`) — not the data list. No new module and no new dependency.
- UX-DR002: Put **every** theme rule under one wrapper CSS class (`.cw_theme_prl10n`), applied **only** to the module's own model screens (the Tax Bracket, Wage Component Set, and Employee Wage Line views, and CW-owned payslip/run views and reports). **Never** add the wrapper to extended Odoo views (Employee, Contract, Salary Rule) — Odoo's own pages must look unchanged.
- UX-DR003: Define the pastel colours as CSS variables for light mode (the page root, `:root`) and dark mode (Odoo's dark-mode class, `.o_dark_mode`), reusing cw_theme's palette (lavender/violet accent; mint/peach/sky/rose support tints). The colours are copied into this module; cw_theme stays a reference only, not a dependency.
- UX-DR004 (deferred): Portal-page styling (the portal counterpart in cw_theme, `.cw-portal`) is out of scope for v1.0R and revisited with payslip distribution (OQ-01); only backend styling ships in v1.0R.

### FR Coverage Map

- FR001: Epic 2 — Run monthly payroll for all employees in one action.
- FR002: Epic 2 — Ordered salary-rule chain (Seq 10–150) with hidden helper rules.
- FR003: Epic 2 — Gross pay (`TOTAL_LOON`) = wage + natura-loon.
- FR004: Epic 2 — Four overtime types as named `ALW` lines.
- FR005: Epic 2 — BVZ health premium (employer 9.3% / employee 4.3%, yearly cap).
- FR006: Epic 2 — AOV/AWW premium (cumulative, ceiling, 1% surcharge).
- FR007: Epic 2 — AVBZ long-term-care premium on the AVBZ-capped AOV base.
- FR008: Epic 2 — Loonbelasting table lookup (`TAX_INC`) + above-ceiling rate.
- FR009: Epic 2 — Standard basiskorting plus employee-specific tax credits.
- FR010: Epic 2 — Bijzondere beloningen marginal-rate tax (AD-21).
- FR011: Epic 2 — ZV (1.9%) and OV (risk-class) employer premiums on the monthly cap.
- FR011b: Epic 2 — Lei di Bion exempt overtime (0%/0%, AD-23).
- FR012: Epic 2 — Net pay (`NET`) and untaxed reimbursements (`NONTAXED`).
- FR013: Epic 2 — Informational total employer cost (`TOTAL_ER_COST`).
- FR014: Epic 2 — Per-employee enable/disable gate on wage lines.
- FR015: Epic 1 — Three-tier wage-component model (Tiers 1/2/3).
- FR016: Epic 1 — Apply wizard copies a Tier 2 set into independent Tier 3 lines.
- FR017: Epic 1 — Dated, append-only statutory data stores (SVB params, tax brackets, lb-tabel).
- FR018: Epic 3 — Year-to-date totals recomputed on close (model stood up empty in Epic 1; read by Epic 2 for cumulative premiums).
- FR019: Epic 1 — Employee tax-credit fields, beschikking, and contract OV%.
- FR020: Epic 3 — Run/payslip stage lifecycle with herberekening.
- FR021: Epic 3 — Close: confirm, lock, recompute YTD, post journal, publish reports.
- FR022: Epic 3 — Balanced journal entry by construction (`account.move`).
- FR023: Epic 4 — Payslip PDF (report A-01).
- FR024: Epic 4 — Wage-tax return (B-01) and SVB premium return (B-02), whole XCG.
- FR025: Epic 4 — Balanced journal-entry summary (report B-05).
- FR026: Epic 1 — Four least-privilege security roles.
- FR027: Epic 1 — Own-payslip record rule (`employee_id.user_id = user`).
- FR028: Epic 3 — Automatic run membership / contract-period exclusion.
- FR029: Epic 1 — Contract start (required) and end (optional) dates.
- FR030: Epic 3 — Senior-only payslip distribution after close.
- FR031: Epic 1 — Manager CSV upload of the lb-maandtabel (annual + mid-year correction).
- FR032: Epic 5 — Seed CW vacation leave type and public-holiday calendar.
- FR033: Epic 5 — Compute yearly entitlement from `resource.calendar` days/week.
- FR034: Epic 5 — Grant yearly allocation on 1 January and prorate mid-year starts.
- FR035: Epic 5 — Carryover cap, lapse excess, and superannuate after long absence.
- FR036: Epic 5 — Termination payout of unused statutory days at day-wage.

## Epic List

### Epic 1: Module Foundation, Configuration & Security
A payroll admin can install the module, load and maintain all statutory rates and tables, build reusable wage-component sets, assign them to employees, capture employee and contract tax data, and operate under least-privilege roles — everything needed before a payslip is computed. Stands up the greenfield module skeleton, the three-tier wage-component model, the dated statutory data stores (with CSV import and 2026 seed data), the per-year `hr.wage.component.ytd` model (empty), the scoped theme, and the Dutch translation.
**FRs covered:** FR015, FR016, FR017, FR019, FR026, FR027, FR029, FR031
**ARs / UX-DRs:** AR001, AR014, AR015, AR016, AR022, AR023, UX-DR001, UX-DR002, UX-DR003

### Epic 2: Statutory Payroll Calculation Engine
A correct monthly payslip computes for any representative employee — standard, BVZ-exempt, above-ceiling, and with special remuneration — matching the official 2026 Belastingdienst/SVB publications within XCG 0.02. Implements the ordered salary-rule chain and all statutory components: gross pay, overtime, the SVB premiums (BVZ, AOV/AWW, AVBZ, ZV/OV), loonbelasting with tax credits, bijzondere beloningen, Lei di Bion exempt overtime, net pay, employer cost, and the enable/disable gate. Computes a single payslip independently of the batch lifecycle.
**FRs covered:** FR001, FR002, FR003, FR004, FR005, FR006, FR007, FR008, FR009, FR010, FR011, FR011b, FR012, FR013, FR014
**ARs:** AR002, AR003, AR004, AR005, AR006, AR007, AR008, AR009, AR012, AR013, AR017, AR020, AR021, AR024

### Epic 3: Run Lifecycle, Accounting & Distribution
A payroll manager runs the full monthly cycle: generate the batch (automatically excluding employees with no worked hours or an ended contract), recalculate as needed, then close once to commit the year-to-date totals and post a balanced journal entry, and finally distribute payslips. Close is the single commit point; reopening reverses the journal entry and re-close stays correct.
**FRs covered:** FR018, FR020, FR021, FR022, FR028, FR030
**ARs:** AR010, AR011, AR019

### Epic 4: Statutory Reports
Each closed run produces the official Curaçao documents and filings: the payslip PDF (A-01), the monthly wage-tax return (B-01) and SVB premium return (B-02) in whole XCG, and the balanced journal-entry summary (B-05).
**FRs covered:** FR023, FR024, FR025

### Epic 5: Statutory Vacation Accrual & Balance (v1.1R)
A payroll manager can track Curaçao statutory paid vacation for each employee: yearly entitlement based on contracted days per week, prorated first-year grants, deduction when leave is taken, carryover cap and lapse, and payout of unused days on termination. Built on native `hr_holidays` with a thin CW localization layer; full design in `docs/design/cw-vacation-accrual-v1.1R.md`.
**FRs covered:** FR032, FR033, FR034, FR035, FR036
**ARs:** AR014 (seed data), AR015 (seed data), AR023 (schema-migration discipline), AR024 (dated data selection is not used here; entitlement is computed from `resource.calendar`)

## Epic 1: Module Foundation, Configuration & Security

A payroll admin can install the module, load and maintain all statutory rates and tables, build reusable wage-component sets, assign them to employees, capture employee and contract tax data, and operate under least-privilege roles — everything needed before a payslip is computed.

### Story 1.1: Greenfield module skeleton and manifest

As a payroll admin,
I want to install the `l10n_cw_hr_payroll` module on Odoo 19 Enterprise,
So that the Curaçao payroll framework is available without errors.

**Acceptance Criteria:**

- **Given** a clean Odoo 19 Enterprise database with `hr_payroll` installed, **When** I install `l10n_cw_hr_payroll`, **Then** it installs without error and reports version `19.0.0.1.0`, country `cw`, license `OPL-1`, `application=False`, and `auto_install=False`. (AR014)
- **Given** the manifest, **When** inspected, **Then** `depends` = `hr, hr_contract, hr_holidays, hr_payroll, hr_payroll_account, hr_attendance` with no theme dependency added. (AR014)
- **Given** the package layout, **When** inspected, **Then** directories follow the three-layer boundaries (Localization ← Application ← Reports) per Tech Design §13. (AR001)
- **Given** the freshly installed skeleton, **Then** no statutory rate, ceiling, or threshold is hard-coded in Python. (AR006)

### Story 1.2: Scoped theme and Dutch i18n scaffolding

As a payroll admin,
I want the module's own screens styled with the `cw_theme_prl10n` theme and a Dutch interface,
So that the module looks consistent and reads in Dutch without altering Odoo's standard pages.

**Acceptance Criteria:**

- **Given** the manifest `assets` entry, **When** the backend loads, **Then** `static/src/scss/cw_theme_prl10n.scss` is bundled into `web.assets_backend` (not the data list). (UX-DR001, AR014)
- **Given** any theme rule, **Then** it is nested under the `.cw_theme_prl10n` wrapper and applied only to the module's own model screens; extended Odoo views (Employee, Contract, Salary Rule) render unchanged. (UX-DR002)
- **Given** light and dark mode, **Then** the pastel palette is defined as CSS variables under `:root` and `.o_dark_mode`. (UX-DR003)
- **Given** `i18n/nl.po`, **Then** the module's UI strings have Dutch translations and statutory terms keep their official form (e.g. `basiskorting`, not `basisaftrek`). (AR016)

### Story 1.3: Security roles and own-payslip record rule

As a system administrator,
I want four least-privilege roles and an own-payslip record rule,
So that each user can access only what their role permits.

**Acceptance Criteria:**

- **Given** the security data, **Then** four groups exist: Employee, Payroll User, Payroll Manager, and Accountant. (FR026)
- **Given** an Employee user, **When** they open payslips, **Then** a record rule limits them to records where `employee_id.user_id = user`. (FR027)
- **Given** each custom model, **Then** `ir.model.access` entries grant least-privilege CRUD aligned to the four roles.
- **Given** the most senior existing role is Payroll Manager, **Then** no new group is introduced (the distribution gate reuses `group_l10n_cw_payroll_manager`). (AR019)

### Story 1.4: Dated statutory data models and lookup methods

As a payroll admin,
I want dated, append-only statutory data models with deterministic lookup methods,
So that rates and tables are maintained as data and read reproducibly by effective date.

**Acceptance Criteria:**

- **Given** the models, **Then** `hr.svb.parameters` (one per year), `hr.tax.bracket` (dated, `tax_type`-keyed), and `hr.loonbelasting.tabel` (header) + `hr.loonbelasting.tabel.lijn` (rows) exist. (FR017, AR006, AR024)
- **Given** a `tax_type` and a date, **When** `compute_tax` is called, **Then** it returns the dated Belastingdienst scalar rounded to 2 decimals; `lookup_marginal_rate` returns the single bijzondere band rate; `lookup_loonbelasting` returns the periodic raw loonbelasting. (AR012)
- **Given** multiple `lb-tabel` headers for a `period_type`+`year`, **When** `lookup_loonbelasting` runs for a date, **Then** it selects active headers with `valid_from ≤ date_to`, ordered by `valid_from` desc then `id` desc. (AR024)
- **Given** a required record or table missing for the effective date, **Then** a `UserError` is raised (fail-loud), never a silent 0. (AR021)
- **Given** a superseded value, **Then** it is closed via `valid_to` and never deleted (append-only), and schema changes ship migrations preserving history. (AR023)
- **Given** national statutory data, **Then** these models are global (no `company_id`). (AR022)

### Story 1.5: Seed 2026 statutory data

As a payroll admin,
I want the 2026 statutory rates seeded on install,
So that calculations reconcile to the official 2026 publications out of the box.

**Acceptance Criteria:**

- **Given** module install, **Then** a 2026 `hr.svb.parameters` record is seeded with all SVB premium rates, the AOV surcharge, and the ceilings (BVZ 150,000/yr, AOV/AWW 100,000/yr, AVBZ 606,247.08/yr, ZV/OV 7,146.10/mo). (AR015)
- **Given** the bijzondere beloningen table, **Then** 6 bands are seeded: 0→9.75%, 43,500→15%, 58,000→23%, 86,900→30%, 123,100→37.5%, 181,000→46.5%. (AR015)
- **Given** the Belastingdienst scalars, **Then** basiskorting 2,915/yr, verwervingskosten 500/yr, and the toeslagen are seeded as dated `hr.tax.bracket` records with `valid_from = 2026-01-01`. (AR013, AR015)
- **Given** the seeds, **Then** no rate literal is hard-coded in salary-rule Python. (AR006)

### Story 1.6: Loonbelasting table CSV import and versioning

As a Payroll Manager,
I want to upload the Belastingdienst lb-maandtabel via CSV,
So that annual tables and mid-year corrections are maintained without a code deploy.

**Acceptance Criteria:**

- **Given** a CSV, **When** I import it into `hr.loonbelasting.tabel` / `.lijn` via the standard Odoo import action, **Then** a header plus rows are created (one row per `wage_from`, maandtabel step XCG 5.00). (FR031, AR024)
- **Given** the new year's table is absent at first run, **Then** the prior year's still-open table is used until the new one arrives. (FR031)
- **Given** a mid-year correction uploaded as a new header for the same year, **Then** the selection rule picks it (latest `valid_from`, then highest `id`) and herberekening on prior periods picks it up automatically. (FR031, AR024)
- **Given** the 2026 maandtabel seed, **Then** ≈ 3,335 rows are loaded (`period_type = maand`, `valid_from = 2026-01-01`). (AR015)
- **Given** `TAX_INC` above the table ceiling (XCG 16,670/mo for 2026), **Then** `lookup_loonbelasting` applies `ceiling_tax + 46.5% × excess`. (AR024)

### Story 1.7: Three-tier wage-component model

As a payroll admin,
I want the Tier 2 set and Tier 3 employee wage-line models with views,
So that I can define reusable component templates and per-employee wage lines.

**Acceptance Criteria:**

- **Given** the models, **Then** `hr.wage.component.set` (+ set line) and `hr.employee.wage.line` exist with list/form/menu views under the Dutch menu (Salarisadministratie → Configuratie). (FR015)
- **Given** the Tier 1 layer, **Then** `hr.salary.rule` carries a `singleton` boolean (default `True`) controlling whether a wage component may be applied more than once to the same employee. (FR015)
- **Given** a Tier 3 wage line, **Then** it carries `enabled` and `active` flags and a `salary_rule_id` link. (AR007, AR008)
- **Given** the never-gate base rules, **Then** the model design supports them always running regardless of `enabled`. (AR007)
- **Given** the module's own views, **Then** they carry the `.cw_theme_prl10n` wrapper. (UX-DR002)

### Story 1.8: Apply wizard for wage-component sets

As a payroll admin,
I want to apply a Tier 2 set to one or more employees,
So that independent Tier 3 wage lines are created without later coupling.

**Acceptance Criteria:**

- **Given** a set and selected employees, **When** I run the apply wizard, **Then** independent Tier 3 `hr.employee.wage.line` records are created as a one-time copy. (FR016, AR009)
- **Given** a later edit to the set, **Then** existing Tier 3 lines do not change. (AR009)
- **Given** a created Tier 3 line, **Then** `salary_rule_id` is read-only. (AR009)

### Story 1.9: Employee and contract statutory fields

As a payroll admin,
I want tax and contract fields on the employee and contract,
So that per-employee statutory inputs and the contract period are captured.

**Acceptance Criteria:**

- **Given** `hr.employee`, **Then** the tax-credit fields (alleenverdieners-, kinder-, ouderentoeslag) and the beschikking input exist. (FR019)
- **Given** `hr.contract`, **Then** an OV% (gevarenklasse) field exists as an interim Float. (FR019)
- **Given** `hr.contract`, **Then** a required start date and an optional end date exist; permanent contracts with no end date are allowed. (FR029)
- **Given** these are extended Odoo views, **Then** the `.cw_theme_prl10n` wrapper is NOT applied. (UX-DR002)

### Story 1.10: Year-to-date totals model

As a payroll admin,
I want the year-to-date totals model in place,
So that cumulative premiums can be read and the close action can write totals later.

**Acceptance Criteria:**

- **Given** the model, **Then** `hr.wage.component.ytd` exists keyed per employee, component, and year, with `ytd_amount`, `last_updated`, and `last_payslip_id`. (FR018)
- **Given** company scoping, **Then** the YTD model is company-scoped via `company_id`. (AR022)
- **Given** v1.0R, **Then** no writes occur here yet — writes happen only at run close (Epic 3) and reads happen in the calculation engine (Epic 2). (AR010)
- **Given** the module's own view, **Then** it carries the `.cw_theme_prl10n` wrapper. (UX-DR002)

## Epic 2: Statutory Payroll Calculation Engine

A correct monthly payslip computes for any representative employee — standard, BVZ-exempt, above-ceiling, and with special remuneration — matching the official 2026 Belastingdienst/SVB publications within XCG 0.02. Implements the ordered salary-rule chain (Seq 10–150) and all statutory components, and computes a single payslip independently of the batch lifecycle.

### Story 2.1: Salary structure, categories, and the ordered rule chain

As a payroll admin,
I want the monthly salary structure, the categories, the ordered salary-rule scaffolding, and gross pay,
So that a payslip computes gross pay in the correct evaluation order and later statutory rules have a foundation to build on.

**Acceptance Criteria:**

- **Given** seed data, **Then** the monthly structure type (`CWMONTHLY`) and the standard-staff structure (`CWSTAFF`) exist with the categories `BASIC`, `ALW`, `DED`, and `ER`. (AR003, AR015)
- **Given** the rule chain, **Then** rules evaluate in strict ascending Sequence (10–150), helper rules are hidden from the payslip (`appears_on_payslip = False`), and a rule reads only earlier results (`rules.CODE.amount`, `categories.X`). (FR002, AR004)
- **Given** the gross-pay rule, **Then** `TOTAL_LOON` (Seq 10) = monthly contract wage + benefits in kind (natura-loon), posted positive to `BASIC`. (FR003, AR002)
- **Given** the earning / wage-line model, **Then** the exclusion flags `is_bijzondere_beloning` and `is_lei_di_bion_exempt` exist on earnings, defaulting to `False`, so later base rules can honour them. (FR010, FR011b)
- **Given** the sign convention, **Then** base and employer amounts are positive and deductions negative. (AR002)

### Story 2.2: Four overtime types as named allowance lines

As a payroll admin,
I want the four overtime types computed as separate named payslip lines,
So that weekday, Saturday, Sunday, and public-holiday overtime are itemised and included in pay.

**Acceptance Criteria:**

- **Given** entered hours and a per-employee rate, **Then** `OVT_WD` (Seq 11), `OVT_SAT` (Seq 12), `OVT_SUN` (Seq 13), and `OVT_PH` (Seq 14) each compute a named line in `ALW`. (FR004, AR003)
- **Given** the overtime defaults, **Then** they apply the confirmed default rates (150/150/200/200), pending final confirmation (OQ-03). (FR004, AR018)
- **Given** an overtime earning, **Then** it may carry `is_bijzondere_beloning` (incidenteel) or `is_lei_di_bion_exempt`, chosen by the payroll manager, with no frequency threshold in the engine. (FR010, FR011b)

### Story 2.3: BVZ health premium

As a payroll admin,
I want the BVZ health premium computed on the yearly-capped premium base,
So that the employer and employee BVZ contributions match the official 2026 SVB table.

**Acceptance Criteria:**

- **Given** the premium base, **Then** `BVZ_PREM_INC` (Seq 20, never-gated) = `categories.BASIC + categories.ALW`, excluding `is_lei_di_bion_exempt` earnings and including `is_bijzondere_beloning`. (FR005, AR005, AR007, AR017)
- **Given** the employer share, **Then** `BVZ_ER` (Seq 30, hidden) = 9.3% of the BVZ base capped cumulatively at XCG 150,000/yr, posted to `ER` (excluded from NET). (FR005, AR005)
- **Given** the employee share, **Then** `BVZ_EMP` (Seq 40) = 4.3% flat on the capped base, negative in `DED`. (FR005, AR002)
- **Given** the rate and ceiling, **Then** they are read from the per-year `hr.svb.parameters` record — no literal in Python. (FR017, AR006)
- **Given** `enabled = False` on the BVZ employee wage line, **Then** `BVZ_EMP` returns 0.00 while `BVZ_PREM_INC` still runs. (FR014, AR007)

### Story 2.4: AOV/AWW premium with above-ceiling surcharge

As a payroll admin,
I want the AOV/AWW premium computed cumulatively up to the annual ceiling plus the 1% surcharge above it,
So that a once-yearly lump is charged only on remaining headroom and high earners pay the surcharge.

**Acceptance Criteria:**

- **Given** the base, **Then** `AOV_PREM_INC` (Seq 50, never-gated) = `categories.BASIC + categories.ALW` (same exclusions as BVZ). (FR006, AR007, AR017)
- **Given** the employee premium, **Then** `AOV_AWW_EMP` (Seq 60) = 6.5% computed cumulatively on the YTD premie-loon capped at XCG 100,000/yr minus premium already withheld, negative in `DED`. (FR006, AR005)
- **Given** the employer premium, **Then** `AOV_AWW_ER` (Seq 61, hidden) = 9.5% on the same capped base, in `ER`. (FR006)
- **Given** YTD income above the ceiling, **Then** `AOV_AWW_1PCT` (Seq 62) applies a 1% employee surcharge on the excess and is 0.00 for employees below the ceiling. (FR006)
- **Given** the rates, ceiling, and surcharge, **Then** all are read from `hr.svb.parameters`. (FR017, AR006)

### Story 2.5: AVBZ long-term-care premium

As a payroll admin,
I want the AVBZ premium computed on the AOV base capped at the AVBZ ceiling,
So that long-term-care contributions match the 2026 SVB table.

**Acceptance Criteria:**

- **Given** the employee premium, **Then** `AVBZ_EMP` (Seq 70) = 1.5% flat on `AOV_PREM_INC` capped cumulatively at XCG 606,247.08/yr, negative in `DED`. (FR007, AR005)
- **Given** the employer premium, **Then** `AVBZ_ER` (Seq 71, hidden) = 0.5% on the same capped base, in `ER`. (FR007)
- **Given** the rates and ceiling, **Then** they are read from `hr.svb.parameters`. (FR017, AR006)
- **Given** `enabled = False`, **Then** `AVBZ_EMP` returns 0.00 without breaking the chain. (FR014, AR007)

### Story 2.6: Fiscal wage base and raw loonbelasting lookup

As a payroll admin,
I want the taxable wage base and the raw wage tax looked up from the official loonbelasting table,
So that loonbelasting reconciles to the 2026 Belastingdienst maandtabel including above-ceiling wages.

**Acceptance Criteria:**

- **Given** the base, **Then** `TAX_INC` (Seq 80, never-gated) = gross − verwervingskosten (41.67/mo forfeit) − the deductible AOV employee premium − the employee pension premium (`inputs.PENSION_EMP`), and excludes `is_bijzondere_beloning` and `is_lei_di_bion_exempt` earnings. (FR008, AR013)
- **Given** an employee pension premium, **Then** it is a per-period payslip input (`PENSION_EMP`), entered by the payroll user, deducted **only** from `TAX_INC` as a loonbelasting aftrekpost and **not** from the SVB premie-loon bases — the BVZ/AOV premiegrondslag is the *zuivere opbrengst van arbeid* before persoonlijke aftrekposten (Landsverordening BVZ → LvIB 1943 Art. 3(4)). (FR008)
- **Given** the raw tax, **Then** `LOONBEL_RAW` (Seq 90, never-gated) = `lookup_loonbelasting(TAX_INC, 'maand', payslip.date_to)` using key `floor(TAX_INC / 5) × 5`. (FR008, AR024, AR020)
- **Given** `TAX_INC` above the table ceiling (XCG 16,670/mo for 2026), **Then** `LOONBEL_RAW = ceiling_tax + 46.5% × excess`; e.g. wage 20,000 → 4,862.91 + 46.5% × 3,330 = XCG 6,411.36. (FR008, AR024)
- **Given** a missing table for the effective date, **Then** a `UserError` is raised (fail-loud), never a silent 0. (AR021)

### Story 2.7: Loonbelasting with tax credits

As a payroll admin,
I want the tax credits applied to the raw wage tax,
So that every employee receives the basiskorting plus any personal credits, floored at zero.

**Acceptance Criteria:**

- **Given** the standard credit, **Then** `LOONBEL` (Seq 100) subtracts the basiskorting (2,915/yr = 242.92/mo) from `LOONBEL_RAW` as a monetary deduction from tax (not from income), for every employee. (FR009, AR013)
- **Given** employee-specific credits, **Then** the alleenverdieners-, kinder-, and ouderentoeslag are subtracted from tax from employee fields. (FR009)
- **Given** the maandtabel is published exclusief basiskorting, **Then** the basiskorting is subtracted here and not assumed already in the table. (FR008)
- **Given** a worked example `TAX_INC` = 3,245/mo, **Then** `LOONBEL` = −(316.39 − 242.92) = −XCG 73.47, negative in `DED` and floored at 0. (FR008)

### Story 2.8: Bijzondere beloningen extra tax

As a payroll admin,
I want special remuneration taxed by the bijzondere-beloningen marginal-rate table,
So that vakantiegeld, bonuses, and incidental overtime are taxed once by their own table.

**Acceptance Criteria:**

- **Given** an `is_bijzondere_beloning` earning, **Then** it stays in NET and in the SVB premium base but is excluded from `TAX_INC`, and `EXTRA_TAX` (Seq 110) = `lookup_marginal_rate(jaarloon)` × the special-remuneration amount, negative in `DED`. (FR010, AR012)
- **Given** the rate, **Then** it is fixed once per tax year from the prior-year jaarloon (annualised if partial; expected jaarloon for new hires) with a payroll-manager override, stored per (employee, year), and the applied rate is recorded on the payslip line. (FR010)
- **Given** a jaarloon, **Then** `lookup_marginal_rate` returns the single band rate (no accumulation) from the 6-band 2026 table. (FR010, AR006)

### Story 2.9: Lei di Bion exempt overtime

As a payroll admin,
I want approved Lei di Bion overtime paid free of tax and premiums,
So that up to 10 exempt hours/week under an approved beschikking are paid in full net.

**Acceptance Criteria:**

- **Given** an `is_lei_di_bion_exempt` earning under an approved beschikking, **Then** it is excluded from both `TAX_INC` and the premium bases (0% / 0%) yet still paid in NET. (FR011b)
- **Given** the beschikking is provided and approved by the Payroll Manager (`group_l10n_cw_payroll_manager`), **Then** the exemption applies; without approval, or beyond 10 hrs/week, the overtime falls back to a taxable route (regulier → maandtabel or incidenteel → bijzondere). (FR011b)
- **Given** 10 exempt overuren = XCG 302.90 gross, **Then** net = 302.90; not exempt (bijzondere 9.75%) → net = 273.37. (FR011b)

### Story 2.10: ZV and OV employer premiums

As a payroll admin,
I want the ZV and OV employer premiums computed on the monthly wage cap,
So that sickness and accident contributions match the SVB monthly-capped basis.

**Acceptance Criteria:**

- **Given** the ZV premium, **Then** `ZV_ER` (Seq 120, hidden) = 1.9% on the shared ZV/OV base capped at XCG 7,146.10/month, applied directly (not annualised), in `ER`. (FR011, AR005)
- **Given** the OV premium, **Then** `OV_ER` (Seq 121, hidden) = the contract OV% (gevarenklasse) on the same monthly-capped base, in `ER`. (FR011, FR019)
- **Given** the rates and cap, **Then** the ZV rate and shared cap come from `hr.svb.parameters` and the OV% from the contract. (FR017, AR006)
- **Given** `enabled = False`, **Then** the premium returns 0.00 without breaking the chain. (FR014, AR007)

### Story 2.11: Net pay, untaxed reimbursements, and employer cost

As a payroll admin,
I want net pay, untaxed reimbursements, and the informational employer cost,
So that the payslip shows what the employee is paid and what the employer bears.

**Acceptance Criteria:**

- **Given** the net rule, **Then** `NET` (Seq 130, never-gated) = `categories.BASIC + categories.ALW + categories.DED` (deductions negative); `ER` amounts are excluded. (FR012, AR003, AR007)
- **Given** untaxed reimbursements, **Then** `NONTAXED` (Seq 140) is a separate line after net; amount paid out = net + untaxed. (FR012, AR003)
- **Given** the employer total, **Then** `TOTAL_ER_COST` (Seq 150, never-gated) sums the employer cost informationally, excluded from NET. (FR013, AR007)

### Story 2.12: Enable/disable gate and never-gate set

As a payroll admin,
I want to switch individual premiums and taxes on or off per employee,
So that a disabled component returns 0.00 without breaking the calculation while shared bases always run.

**Acceptance Criteria:**

- **Given** the enable gate, **Then** each premium/tax rule checks its `hr.employee.wage.line.enabled`; when `False` it sets `result = 0.00` and skips its logic, and downstream reads 0.00 (never an error or stale value). (FR014, AR007)
- **Given** the never-gate set, **Then** `BVZ_PREM_INC`, `AOV_PREM_INC`, `TAX_INC`, `LOONBEL_RAW`, `NET`, and `TOTAL_ER_COST` always execute regardless of flags. (FR014, AR007)
- **Given** an audit exemption, **Then** a line with `active = True, enabled = False` stays visible but returns 0.00. (AR008)

### Story 2.13: Statutory reconciliation for representative employees

As a payroll admin,
I want a single payslip to reconcile to the official 2026 publications for representative employees,
So that the engine is proven correct before the run lifecycle is built.

**Acceptance Criteria:**

- **Given** a single payslip, **Then** it computes independently of the batch lifecycle. (FR001)
- **Given** a standard employee, **When** the payslip computes, **Then** loonbelasting and all SVB premiums match the 2026 Belastingdienst/SVB publications within XCG 0.02. (NFR001)
- **Given** a BVZ-exempt employee (`enabled = False` on BVZ), **Then** BVZ is 0.00 and NET is undisturbed. (NFR001, FR014)
- **Given** an above-ceiling employee (wage 20,000/mo), **Then** loonbelasting = XCG 6,411.36 and AOV/AVBZ apply their cumulative ceilings and the 1% surcharge. (NFR001, FR008)
- **Given** an employee with special remuneration, **Then** the bijzondere amount is taxed by `EXTRA_TAX` only and stays in the premium base. (NFR001, FR010)

## Epic 3: Run Lifecycle, Accounting & Distribution

A payroll manager runs the full monthly cycle: generate the batch (automatically excluding employees with no worked hours or an ended contract), recalculate as needed, then close once to commit the year-to-date totals and post a balanced journal entry, and finally distribute payslips. Close is the single commit point; reopening reverses the journal entry and re-close stays correct.

### Story 3.1: Run and payslip lifecycle with herberekening

As a payroll manager,
I want to drive a run and its payslips through their stages and recalculate before close,
So that I can review and correct a batch before committing it.

**Acceptance Criteria:**

- **Given** a payroll run, **Then** it moves Draft → To Check → Closed (CONCEPT → TE CONTROLEREN → AFGESLOTEN). (FR020)
- **Given** generating the batch, **Then** a payslip is created for each in-service employee in one action, each moving Draft → To Check → Confirmed (CONCEPT → TE CONTROLEREN → BEVESTIGD), with cancel. (FR020, FR001)
- **Given** a pre-close run, **When** I recalculate (herberekening), **Then** payslip amounts recompute; recompute is allowed only before close. (FR020)

### Story 3.2: Automatic run membership and contract-period exclusion

As a payroll manager,
I want employees with no worked hours or an ended contract left out automatically,
So that the run pays only those in service for the period, with no manual step.

**Acceptance Criteria:**

- **Given** an employee with no worked hours in the period, **Then** they are left out automatically — no payslip, and absent from the run totals and the journal. (FR028)
- **Given** an employee whose contract ended on or before the period, **Then** they are excluded using the contract start / end dates. (FR028, FR029)
- **Given** a permanent contract with no end date, **Then** the employee is included while in service. (FR029)
- **Given** exclusion, **Then** it is never a manual action. (FR028)

### Story 3.3: Close commits once — lock, YTD, journal, reports

As a payroll manager,
I want closing the run to be the single point that commits results,
So that confirming, YTD, the journal, and reports all happen exactly once, together.

**Acceptance Criteria:**

- **Given** `action_close()`, **Then** it confirms and locks the payslips, upserts `hr.wage.component.ytd` (increment per line), posts the `account.move` (draft → posted), and exposes the run reports — the one and only commit point. (FR021, FR018, AR010)
- **Given** the year-to-date totals, **Then** they are recomputed (not blindly added), keyed per employee / component / year and kept across years. (FR018, AR010)
- **Given** close, **Then** the year-to-date totals and the journal are mutated nowhere else. (AR010)

### Story 3.4: Balanced journal entry by construction

As an accountant,
I want each close to post a journal entry that balances by construction,
So that payroll accounting is always correct without manual reconciliation.

**Acceptance Criteria:**

- **Given** close, **Then** the `account.move` has total debit == total credit by construction (every employer-cost debit has a matching payable credit; total loon = net + all employee deductions). (FR022, AR011, NFR005)
- **Given** the general-ledger mapping, **Then** it is configurable per company (account numbers are indicative placeholders) and uses the actual 2-decimal amounts. (FR022, AR011)

### Story 3.5: Controlled reopen and idempotent re-close

As a payroll manager,
I want to reopen a closed run and re-close it safely,
So that corrections never double-count the year-to-date totals or post duplicate or unbalanced journal entries.

**Acceptance Criteria:**

- **Given** a closed run, **When** I reopen it (the only in-app reopen), **Then** the `account.move` is reversed. (AR010)
- **Given** re-close after a correction, **Then** the year-to-date totals are recomputed so they are not double-counted and no duplicate or unbalanced journal is posted. (NFR008, AR010)
- **Given** disaster recovery, **Then** a whole-database restore is out of module scope (a pre-close manual Odoo.sh backup is the operational safety step). (AR010)

### Story 3.6: Senior-only payslip distribution after close

As a payroll manager,
I want distributing payslips to be a separate senior-only action after close,
So that employees receive payslips only when they are explicitly released.

**Acceptance Criteria:**

- **Given** distribution, **Then** it is a separate explicit action restricted to `group_l10n_cw_payroll_manager` (no new group is added). (FR030, AR019)
- **Given** the gate, **Then** it is allowed only after run close plus an explicit "no restore needed" confirmation; closing a run does not distribute. (FR030, AR019)
- **Given** the send channel (email / Employee Portal / app), **Then** it is deferred (OQ-01). (FR030, AR018)

## Epic 4: Statutory Reports

Each closed run produces the official Curaçao documents and filings. Reports are read-only (Reports layer): they read committed amounts and recompute no statutory value.

### Story 4.1: Payslip PDF (A-01)

As an employee,
I want a payslip PDF in Curaçao layout,
So that I have an official record of my pay and deductions.

**Acceptance Criteria:**

- **Given** a computed payslip, **Then** report A-01 renders a QWeb PDF in Curaçao layout showing the payslip lines. (FR023)
- **Given** the Reports layer, **Then** the report only reads committed amounts and recomputes no statutory value. (FR023)

### Story 4.2: Monthly wage-tax return (B-01)

As a payroll manager,
I want the monthly loonbelasting return per run,
So that I can file the wage tax with the Belastingdienst.

**Acceptance Criteria:**

- **Given** a closed run, **Then** report B-01 shows the monthly loonbelasting totals in whole XCG (decimals dropped / truncated, not rounded). (FR024)
- **Given** the Reports layer, **Then** B-01 reads committed amounts and computes nothing. (FR024)

### Story 4.3: SVB premium return (B-02)

As a payroll manager,
I want the monthly SVB premium return per run,
So that I can file the premiums with the SVB.

**Acceptance Criteria:**

- **Given** a closed run, **Then** report B-02 shows the SVB premium totals (BVZ, AOV/AWW, AVBZ, ZV, OV) in whole XCG (decimals dropped / truncated). (FR024)
- **Given** the Reports layer, **Then** B-02 reads committed amounts and computes nothing. (FR024)

### Story 4.4: Balanced journal-entry summary (B-05)

As an accountant,
I want the payroll journal-entry summary per run,
So that I can verify the posted entry balances.

**Acceptance Criteria:**

- **Given** a closed run, **Then** report B-05 summarises the balanced journal entry (`account.move`) with total debit == total credit. (FR025, NFR005)
- **Given** the Reports layer, **Then** B-05 reads the posted entry and computes nothing. (FR025)

## Epic 5: Statutory Vacation Accrual & Balance (v1.1R)

A payroll manager can track Curaçao statutory paid vacation for each employee: yearly entitlement based on contracted days per week, prorated first-year grants, deduction when leave is taken, carryover cap and lapse, and payout of unused days on termination. Built on native `hr_holidays` with a thin CW localization layer; full design in `docs/design/cw-vacation-accrual-v1.1R.md`.

### Story 5.1: Seed CW vacation leave type and public holidays

As a payroll admin,
I want the Curaçao statutory vacation leave type and the CW public-holiday calendar seeded on install,
So that public holidays are separate paid free days and never deducted from vacation balance.

**Acceptance Criteria:**

- **Given** module install, **Then** an `hr.leave.type` record `Wettelijke Vakantie (CW)` (`CWVAC`) exists, allocation-required, with day unit and manager validation. (FR032)
- **Given** the seeded public-holiday calendar, **Then** CW public holidays are created as `resource.calendar.leaves` (global time off). (FR032)
- **Given** a leave request spanning a public holiday, **When** it is approved, **Then** the holiday days are not deducted from the vacation balance. (FR032)

### Story 5.2: Compute yearly entitlement from working schedule

As a payroll manager,
I want the yearly vacation entitlement computed from the employee's contracted days per week,
So that the statutory grant is correct for full-time, part-time, and 6-day-week employees.

**Acceptance Criteria:**

- **Given** an employee with a 5-day `resource.calendar`, **When** the annual entitlement is computed, **Then** it equals 15 days. (FR033)
- **Given** a 6-day calendar, **When** the entitlement is computed, **Then** it equals 15 days (capped at 5 days/week), not 18. (FR033)
- **Given** a 4-day calendar, **When** the entitlement is computed, **Then** it equals 12 days. (FR033)
- **Given** a 20-hour/week employee spread over 5 days, **When** the entitlement is computed, **Then** it equals 15 days (hours do not reduce the count). (FR033)

### Story 5.3: Grant yearly allocation and prorate mid-year starts

As a payroll manager,
I want the vacation allocation granted each year on 1 January and prorated for new hires,
So that every employee receives the correct statutory days without manual entry.

**Acceptance Criteria:**

- **Given** an active employee at year start, **When** the scheduled action runs on 1 January, **Then** an `hr.leave.allocation` is created for the full yearly entitlement. (FR034)
- **Given** an employee who starts on 1 July, **When** the first grant runs, **Then** the allocation is prorated per the basis resolved by OQ-11. (FR034)
- **Given** an existing allocation for the year, **When** the scheduled action runs again, **Then** it updates rather than duplicates the allocation. (FR034)

### Story 5.4: Carryover cap and lapse on long absence

As a payroll manager,
I want accumulated vacation capped, excess days lapsed, and prior-year rights superannuated after long absence,
So that the balance always reflects the statutory maximum and legal superannuation rules.

**Acceptance Criteria:**

- **Given** a 5-day employee with a carried-forward balance, **When** the carryover cap is enforced, **Then** the total balance is capped at 30 days (`6 × 5`). (FR035)
- **Given** a balance above the cap, **When** the cap is enforced, **Then** excess days are lapsed and recorded. (FR035)
- **Given** an employee absent ≥ 6 months due to sickness in a year, **When** the year ends, **Then** prior-year vacation rights for that year superannuate. (FR035)
- **Given** an employee absent ≥ 6 weeks due to legal obligations in a year, **When** the year ends, **Then** prior-year vacation rights for that year superannuate. (FR035)

### Story 5.5: Payout unused vacation days on termination

As a payroll manager,
I want unused statutory vacation days paid out on termination at the statutory day-wage,
So that the final settlement complies with the Vakantieregeling 1949.

**Acceptance Criteria:**

- **Given** a 5-day employee with 5 unused statutory days and monthly wage XCG 3,250, **When** a final settlement is processed, **Then** `VAC_PAYOUT` = `3,250 × 3 / 65 × 5` = XCG 750.00. (FR036)
- **Given** a 6-day employee with the same wage and days, **When** the payout is computed, **Then** it uses `× 3 / 78`. (FR036)
- **Given** a partial day owed, **When** the payout is computed, **Then** it rounds up to a whole day. (FR036)

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

- loonbelasting — wage tax; a periodic employer withholding that is a prepayment of the employee's annual inkomstenbelasting. Computed via the official lb-*tabel (published by Belastingdienst Curaçao per Ministerial Regulation), not the Schijventarief (which is the annual inkomstenbelasting bracket table).
- inkomstenbelasting — annual income tax; covers all income types (wages, interest, rental, etc.) and is settled by the taxpayer on their annual return. The Schijventarief is the bracket table for this tax.
- loonbelastingkaart — annual wage-tax card per employee showing cumulative loonbelasting withheld; deferred to v1.1R.
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
- `hr.tax.bracket` — Tax Bracket model (dated statutory data for bijzondere beloningen marginal rates and the Belastingdienst scalars: basiskorting, verwervingskosten, toeslagen). SVB premiums are not here — see `hr.svb.parameters`.
- `hr.svb.parameters` — per-year SVB parameter record (one per year): all SVB premium rates, the AOV surcharge, and the ceilings, mirroring the annual SVB table (AD-22).
- `hr.loonbelasting.tabel` — Loonbelasting Table header (fields: `name`, `period_type`, `year`, `valid_from`, `valid_to`, `active`; multiple versions per period type + year are supported for corrections).
- `hr.loonbelasting.tabel.lijn` — Loonbelasting Table rows (one record per wage point; lookup source).
- `hr.wage.component.ytd` — Year-to-Date totals model.
- `account.move` — Odoo journal entry.
- `mail.thread` — Odoo mixin providing the change log (chatter).
- Salary-rule codes — `TOTAL_LOON` (gross pay), `NET` (net pay), `NONTAXED` (untaxed reimbursements), `TOTAL_ER_COST` (employer cost), and the hidden bases `BVZ_PREM_INC`, `AOV_PREM_INC`, `TAX_INC`, `LOONBEL_RAW`.
- Categories — `BASIC` (basic pay), `ALW` (allowances), `DED` (deductions), `ER` (employer cost).
- Fields and flags — `appears_on_payslip` (show on payslip), `enabled` (counts in the calculation), `active` (visible), `valid_from` / `valid_to` (rate validity dates), `salary_rule_id` (linked rule), `tax_type` (rate type), `employee_id.user_id` (owner link used by the record rule).
- `tax_type` values — `bijzondere_beloning`, `basiskorting`, `verwervingskosten`, and the toeslag types. (SVB premiums are no longer `tax_type` values — they moved to `hr.svb.parameters`, AD-22. Loonbelasting uses `hr.loonbelasting.tabel`.)
- `compute_tax` — method on `hr.tax.bracket` returning the dated Belastingdienst scalar (basiskorting, verwervingskosten, toeslag) for a `tax_type` and date.
- `lookup_marginal_rate` — method on `hr.tax.bracket` returning the single bijzondere-beloningen band rate whose range contains the jaarloon (no accumulation); used by EXTRA_TAX (AD-21).
- `lookup_loonbelasting` — method on `hr.loonbelasting.tabel` returning the periodic loonbelasting for a given wage, period type, and effective date. Selects the active table version by `valid_from desc, id desc` (latest effective, then latest upload); applies the above-ceiling rule when needed; raises `UserError` if no table is found.
- `action_close()` — the run-close action; the single commit point.
- `CWMONTHLY` / `CWSTAFF` — the monthly structure type / standard-staff salary structure.
- Manifest keys — `depends`, `version`, `country`, `license`, `application`, `auto_install`, `assets`, `data`.
- `web.assets_backend` — Odoo backend asset bundle.
- `.cw_theme_prl10n` — theme wrapper CSS class; `:root` / `.o_dark_mode` — light / dark mode token scopes; `.cw-portal` — portal scope (deferred).
- `static/src/scss/cw_theme_prl10n.scss` — the theme stylesheet; `i18n/nl.po` — the Dutch translation file.
