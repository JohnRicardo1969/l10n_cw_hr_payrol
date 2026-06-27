# l10n_cw_hr_payroll

## Product Requirements Document — Curaçao Payroll Localization for Odoo 19 Enterprise

| Field | Value |
|---|---|
| Document version | 1.0D (Draft) |
| Date | June 15, 2026 |
| Status | Draft — pending stakeholder review |
| Primary scope | v1.0R (initial production release) |
| Source document | Technical Design Document v3.0D |
| Target platform | Odoo 19 Enterprise on Odoo.sh |
| Localization country | Curaçao (`cw`) |
| Confidentiality | Internal / Partner use only |

# Executive Summary

`l10n_cw_hr_payroll` is a custom Odoo 19 Enterprise payroll localization module for Curaçao. It implements the full statutory payroll framework governed by the Belastingdienst Curaçao (wage tax — loonbelasting) and the Sociale Verzekeringsbank (SVB — AOV/AWW, AVBZ, BVZ, ZV, OV premiums), built on top of Odoo's native `hr_payroll` engine.

The module follows Odoo's official localization pattern, analogous to `l10n_be_hr_payroll` and `l10n_in_hr_payroll`, making it the first formally structured payroll localization for Curaçao on the Odoo platform.

All calculation logic executes inside Odoo with no external payroll service dependency. Statutory rates are stored as dated data records rather than hardcoded, so rate updates require no code deployment. A three-tier wage component model separates global rule definitions, company-level template sets, and per-employee assignments. The canonical calculation sequence follows the official Curaçao payroll pseudocode step by step, with each pseudocode step mapping to one or more Odoo salary rules in strict sequence order.

This PRD describes the requirements for the initial production release (v1.0R), which covers monthly payroll only. Later pay periods (bi-weekly, semi-monthly, weekly) and advanced features are documented in the release roadmap but are out of scope for v1.0R.

# Problem Statement

No formally structured, statutory-compliant payroll localization for Curaçao exists on the Odoo platform. Organizations on Curaçao running Odoo must either process payroll outside Odoo and manually reconcile journal entries, or use generic Odoo salary rules that do not implement Curaçao-specific premium structures, sliding scales, tax brackets, or statutory deduction sequences.

Both approaches carry material risk. Manual processing is error-prone and labour-intensive, and reconciling externally calculated payroll back into the Odoo general ledger introduces a class of posting errors that are difficult to audit. Generic salary rules silently produce incorrect statutory amounts — for example, omitting the AVBZ low-income threshold of XCG 29,897.44 (a common defect in commercial payroll packages that causes low earners to overpay), or treating toeslagen as income reductions rather than as monetary deductions from the computed tax.

The module eliminates this gap by implementing the complete Curaçao statutory payroll framework inside Odoo, with all logic, rates, and rules derived from the official publications of the Belastingdienst Curaçao and the SVB.

# Goals and Objectives

## Primary Goals

The module is built to satisfy five primary goals.

**Statutory correctness.** Payroll calculations are correct under the current Landsverordening for loonbelasting and all SVB premiums, including sliding scales, ceilings, low-income thresholds, and the above-ceiling AOV surcharge.

**Auditability.** Every calculation step is traceable. Intermediate values are materialized as salary rules, rates are stored as inspectable data records, and all custom models carry a chatter audit trail.

**Operational independence.** Payroll administrators run monthly payroll end to end inside Odoo, without any external payroll service or spreadsheet.

**Regulatory agility.** Rate changes — annual or ad hoc — require no code deployment. They are applied by creating new dated bracket records, leaving historical records intact for accurate recomputation of prior periods.

**Accounting integration.** Closing a payroll run automatically posts a balanced journal entry to the general ledger, with correct debit/credit mapping for every cost and liability account, such that total debit equals total credit by construction.

## Success Measures

The goals above are considered met when the acceptance criteria are satisfied: calculation output reconciles to the official rate publications within rounding tolerance, every run close produces a balanced journal entry, statutory exemptions can be applied per employee without breaking the calculation chain, and rates can be updated without a code release.

# Scope

## In Scope (v1.0R)

The initial production release covers monthly payroll for standard staff contracts. It includes the complete statutory calculation sequence (gross through net and total employer cost), the three-tier wage component model, the per-employee enable/disable mechanism for premiums and taxes, year-to-date accumulation, accounting integration with automatic journal posting, the four overtime types, the monthly wage tax and SVB premium declarations, the payslip PDF, and the four security roles.

## Out of Scope (v1.0R)

The following are explicitly excluded from the initial release. Items with a target version are deferred (see the release roadmap); Cessantia is a permanent exclusion.

| Excluded item | Reason | Target |
|---|---|---|
| Bi-weekly, semi-monthly, weekly payroll | v1.0R is monthly only; other periods need separate tax tables and divisors | v1.1R |
| ZV sick pay processing | Requires decisions on waiting-period tracking and SVB reimbursement, plus `hr_holidays` integration | v1.1R |
| Loan deductions and wage garnishments | Requires an application-layer model and a statutory bestaansminimum decision | v1.1R |
| Verzamelloonstaat CSV export | Statutory annual filing; depends on YTD model and portal spec confirmation | v1.1R |
| Loonbelastingkaart (jaaropgaaf) | Annual per-employee wage tax statement; depends on YTD model | v1.1R |
| Electronic filing with Belastingdienst CW | Portal API not yet publicly documented | v2.0R |
| DGA (directeur-grootaandeelhouder) payroll | Separate tax treatment required | v1.2R |
| Pension fund integrations (APC, FATUM, ENNIA) | External API dependencies not yet scoped | v2.0R |
| Extension to Aruba / Sint Maarten | Similar framework, separate rate structures | v2.0R |
| **Cessantia** | Termination-time obligation under the Cessantialandsverordening, settled directly between employer and employee; not a periodic payroll contribution | Permanent exclusion |

# Platform and Architecture

## Platform Decision

The module requires Odoo 19 Enterprise deployed on Odoo.sh, or an equivalent self-hosted Odoo Enterprise installation. Odoo SaaS is not a supported platform.

| Constraint | Odoo SaaS | Odoo.sh / Self-hosted |
|---|---|---|
| Custom module installation | Not permitted | Supported |
| Python code in salary rules | Not accessible | Full access |
| Custom ORM models | Studio only (`x_` prefix) | Full model definition |
| `hr_payroll` module | Not available | Available (Enterprise) |
| `hr_payroll_account` | Not available | Available (Enterprise) |
| Direct XML data files | Not accessible | Full access |

Odoo.sh specifically provides the CI/CD pipeline, branch-based testing, automated upgrades, and managed infrastructure that a production payroll deployment requires. The Odoo Enterprise license is mandatory because `hr_payroll` and `hr_payroll_account` are Enterprise-only modules not present in Community Edition.

## Layered Module Architecture

The module is organized in three layers on top of the standard Odoo stack (see Figure 1).

### Localization Layer

The localization layer holds the statutory definitions: the `hr.salary.rule` extension (singleton field), the `CWMONTHLY` structure type and `CWSTAFF` structure, all Curaçao salary rules (Steps 10–150), the `hr.tax.bracket` rate model, the employee toeslag fields, and the contract OV percentage field. This layer contains data published by the Belastingdienst Curaçao and SVB.

### Application Layer

The application layer holds the configuration and workflow models: `hr.wage.component.set` and its lines (Tier 2), `hr.employee.wage.line` (Tier 3), `hr.wage.component.ytd`, the `hr.wage.set.apply.wizard`, and all views, menus, and security groups.

### Reports Layer

The reports layer holds the QWeb PDF templates (payslip A-01, declarations B-01 and B-02, journal entry summary B-05) and the CSV generators deferred to v1.1R.

## Module Dependencies

Direct dependencies declared in `__manifest__.py` are `hr`, `hr_contract`, `hr_holidays`, `hr_payroll`, `hr_payroll_account`, and `hr_attendance`. Odoo resolves the transitive dependencies automatically: `resource` (drives working-hour normalization and absence handling), `mail` (provides `mail.thread` and `mail.activity.mixin` for chatter and audit trails), and `account` (provides `account.account`, `account.journal`, and `account.move`).

The full installation order is:

```
base → mail → resource → hr → hr_contract → hr_holidays
→ hr_attendance → account → hr_payroll → hr_payroll_account
→ l10n_cw_hr_payroll
```

# Users and Roles

Four user roles are supported. Role-to-user assignment is a per-organization configuration decision made during onboarding (see Open Questions).

| Role | Odoo Group | Capabilities |
|---|---|---|
| Employee | `group_l10n_cw_employee` | View and download own payslips only |
| Payroll User | `group_l10n_cw_payroll_user` | Compute runs, edit employee wage lines and payslip descriptions, read tax brackets |
| Payroll Manager | `group_l10n_cw_payroll_manager` | Full access including tax bracket management and reopening closed runs |
| Accountant | `group_l10n_cw_accountant` | Read payroll runs and journal entries; no write access to computation |

The Employee group is intended for staff with internal Odoo user access. Portal-only employees are handled separately through the payslip distribution mechanism (see Open Questions).

# User Stories

## Employee

As an employee, I want to view and download my monthly payslip (loonstrook) as a PDF, so that I have a record of my earnings, deductions, and net pay.

## Payroll User

As a payroll user, I want to enter employee-specific monthly inputs (fringe benefits, pension contribution, beschikking, overtime hours, bijzondere beloningen) before running payroll, so that each payslip reflects that employee's actual situation for the period.

As a payroll user, I want to compute payroll for all employees in a run with a single action, so that I do not process payslips individually.

As a payroll user, I want to review computed payslips in a verify state before closing the run, so that I can correct errors before any journal entry is posted.

As a payroll user, I want to disable a specific premium or tax for an individual employee — for example BVZ for someone with approved private health insurance — without removing the rule from the structure, so that the exemption remains visible to auditors.

As a payroll user, I want overtime earnings (weekday, Saturday, Sunday, public holiday) to appear as separate named lines on the payslip, so that the basis for each amount is transparent.

## Payroll Manager

As a payroll manager, I want to update statutory rates by creating new dated bracket records, without writing or deploying code, so that rate changes take effect for the correct periods immediately.

As a payroll manager, I want to apply a wage component template set to one or more employees at onboarding, so that each employee starts with the correct components without line-by-line setup.

As a payroll manager, I want year-to-date totals per wage component per employee to accumulate automatically on every run close, so that annual declarations need no manual aggregation.

## Accountant

As an accountant, I want a balanced journal entry generated automatically when a run is closed, so that payroll costs post to the GL without manual journalizing.

As an accountant, I want to print the wage tax declaration and the SVB premium declaration per run, so that I can file monthly obligations with the Belastingdienst Curaçao and SVB.

# Statutory Calculation Engine

The calculation engine is the core of the module. It is implemented as a sequence of `hr.salary.rule` records evaluated in strict sequence order, mirroring the official Curaçao payroll pseudocode. Computational intermediates that are not printed on the payslip carry `appears_on_payslip = False`.

## Python Computation Context

Each salary rule's `amount_python_compute` block executes with the following context available, and must assign `result`:

| Name | Meaning |
|---|---|
| `employee` | `hr.employee` record |
| `contract` | `hr.contract` record |
| `payslip` | `hr.payslip` record |
| `worked_days` | Worked-days object, accessed by code (e.g. `worked_days.WORK100.number_of_hours`) |
| `inputs` | Payslip inputs, accessed by code (e.g. `inputs.PENSION_EMP.amount`) |
| `categories` | Accumulated category totals (e.g. `categories.BASIC`, `categories.ALW`, `categories.DED`, `categories.ER`) |
| `rules` | Prior rule results (e.g. `rules.BVZ_PREM_INC.amount`) |
| `env` | Odoo environment for ORM queries (e.g. `env['hr.tax.bracket'].search(...)`) |
| `result` | The computed amount for this rule — must be assigned |

By convention, deduction rules return negative values, so that the NET rule can sum categories directly.

## Canonical Sequence Map

The complete v1.0R sequence (Cessantia excluded — see Authoring Assumptions) is:

| Seq | Code | Pseudocode Step | Description | On Payslip |
|---|---|---|---|---|
| 10 | TOTAL_LOON | Step 1 | Gross money earnings + fringe benefits (natura-loon) | Yes |
| 11 | OVT_WD | Step 1 | Weekday overtime (configurable rate, default 150%) | Yes |
| 12 | OVT_SAT | Step 1 | Saturday overtime (configurable rate, default 150%) | Yes |
| 13 | OVT_SUN | Step 1 | Sunday overtime (configurable rate, default 200%) | Yes |
| 14 | OVT_PH | Step 1 | Public holiday overtime (configurable rate, default 200%) | Yes |
| 20 | BVZ_PREM_INC | Step 2 | BVZ premium income base (after deductions) | No |
| 30 | BVZ_ER | Step 3 | BVZ employer 9.3% | Yes |
| 40 | BVZ_EMP | Step 4 | BVZ employee sliding scale 0%–4.3% | Yes |
| 50 | AOV_PREM_INC | Step 5 | AOV/AWW/AVBZ premium income base | No |
| 60 | AOV_AWW_EMP | Step 6 | AOV/AWW employee 6.5% (up to ceiling) | Yes |
| 61 | AOV_AWW_ER | Step 6 | AOV/AWW employer 9.5% (up to ceiling) | Yes |
| 62 | AOV_AWW_1PCT | Step 6 | AOV employee surcharge 1% above ceiling | Yes |
| 70 | AVBZ_EMP | Step 7 | AVBZ employee 0.5% or 1.5% (sliding) | Yes |
| 71 | AVBZ_ER | Step 7 | AVBZ employer 0.5% | Yes |
| 80 | TAX_INC | Step 8 | Fiscal wage base for loonbelasting | No |
| 90 | LOONBEL_RAW | Step 9 | Raw loonbelasting from lb-maandtabel | No |
| 100 | LOONBEL | Step 10 | Loonbelasting after toeslagen deduction | Yes |
| 110 | EXTRA_TAX | Step 11 | Tax on bijzondere beloningen (separate table) | Yes |
| 120 | ZV_ER | Step 12 | ZV employer 1.9% (up to ZV/OV ceiling) | Yes |
| 121 | OV_ER | Step 12 | OV employer variable % (up to ZV/OV ceiling) | Yes |
| 130 | NET | Step 13 | Net salary payable to employee | Yes |
| 140 | NONTAXED | Step 13 | Onbelaste vergoedingen (added to net) | Yes |
| 150 | TOTAL_ER_COST | Step 14 | Total employer cost (informational) | No |

## Step Design Detail

This section describes the intended computation of each step. Annualisation is used wherever a statutory ceiling or threshold is expressed as an annual figure: the periodic (monthly) base is multiplied by 12, the ceiling or scale is applied, and the result is divided back by 12.

### Step 1 — Total Loon and Overtime (Seq 10–14)

`TOTAL_LOON` is the anchor for all downstream calculations: contract wage plus any fringe benefits (`inputs.FRINGE_BENEFITS`). The four overtime rules each compute their amount from the corresponding hours input (`OVT_WD_HRS`, `OVT_SAT_HRS`, `OVT_SUN_HRS`, `OVT_PH_HRS`) and the rate stored on the employee's wage line as `parameter_value`, deriving the hourly rate from the contract wage divided by the normalized monthly hours. Overtime contributes to the ALW category alongside other allowances. An employee with no overtime simply has zero hours entered and the rules evaluate to zero without error.

### Step 2 — BVZ Premium Income Base (Seq 20)

The BVZ base is total loon less the verwervingskosten forfeit (XCG 41.67/month) and the employee pension contribution. The base is then annualised and capped at the BVZ ceiling of XCG 150,000/year before being returned to periodic form. This rule is a shared intermediate and always executes.

### Steps 3–4 — BVZ Employer and Employee (Seq 30, 40)

The employer pays a flat 9.3% of the capped BVZ base. The employee pays on a sliding scale designed to protect low earners: 0% below XCG 12,000/year, graduating through intermediate bands to the full 4.3% above XCG 18,000/year. The employee amount is returned as a negative (deduction) value.

### Step 5 — AOV/AWW/AVBZ Premium Income Base (Seq 50)

The AOV base is total loon less the verwervingskosten forfeit, the employee pension contribution, and the beschikking (tax ruling deduction). It is the shared base for AOV/AWW, the above-ceiling surcharge, and AVBZ, and always executes. The deduction is the employee pension part (werknemersdeel), correcting an error in the original pseudocode that referenced the employer part.

### Step 6 — AOV/AWW (Seq 60, 61, 62)

AOV and AWW are modeled as one combined premium. The employee pays 6.5% (AOV 6% + AWW 0.5%) on the base up to the XCG 100,000/year ceiling. The employer pays 9.5% (AOV 9% + AWW 0.5%) on the same capped base. For income above the ceiling, the employee pays an additional 1% surcharge (`AOV_AWW_1PCT`) on the excess only. The surcharge is zero for most employees and ensures compliance with the Landsverordening for high earners.

### Step 7 — AVBZ (Seq 70, 71)

AVBZ uses the AOV base capped at the AVBZ ceiling of XCG 606,247.08/year. The employee rate is sliding: 0.5% if annual AOV income is below XCG 29,897.44, otherwise 1.5%. The employer rate is a flat 0.5%. Applying the low-income threshold correctly is a deliberate point of difference from many commercial packages that omit it.

### Steps 8–10 — Loonbelasting (Seq 80, 90, 100)

`TAX_INC` is the fiscal wage: the AOV base less the absolute AOV/AWW employee premium. `LOONBEL_RAW` looks up the raw loonbelasting directly from the official Belastingdienst lb-maandtabel (`hr.loonbelasting.tabel`) for the `TAX_INC` value and the payslip period-end date — no annualisation (the table is already period-specific). For wages above the table ceiling (XCG 16,670/month) the above-ceiling extension applies: `ceiling_tax + (TAX_INC − ceiling) × 46.5%` (MR 144 § Algemeen). `LOONBEL` then applies the toeslagen as monetary deductions from the raw tax amount — not as reductions to taxable income — flooring the result at zero and returning it as a negative (deduction) value. The basiskorting (XCG 2,915/year) applies automatically to all employees; the remaining toeslagen are stored as annual amounts on employee fields and divided by 12.

### Step 11 — Extra Tax on Bijzondere Beloningen (Seq 110)

When a bijzondere beloning is present, a marginal rate is selected from a separate rate table based on the employee's annual total loon, and applied only to the bijzondere beloning amount. This is distinct from the regular loonbelasting brackets. The rule returns zero when there is no bijzondere beloning.

### Step 12 — ZV and OV (Seq 120, 121)

ZV and OV are employer-only and share a wage ceiling of XCG 7,146.10/month (XCG 85,753.20/year). Both use the contract base wage (excluding fringe benefits) capped at that ceiling. ZV is a flat 1.9%; OV is variable by gevarenklasse, read from the contract OV percentage field. ZV and BVZ are separate statutory insurances and must not be combined.

### Step 13 — Net and Non-Taxed Amounts (Seq 130, 140)

NET sums the BASIC, ALW, and DED categories (DED being negative). NONTAXED adds onbelaste vergoedingen, which are not subject to any premium or tax; they appear as a separate payslip line and post to a dedicated GL account.

### Step 14 — Total Employer Cost (Seq 150)

An informational aggregate of total loon plus the employer-contribution category. It does not affect net pay and is used for labour-cost reporting only.

## Enable / Disable Mechanism

Every salary rule that maps to an `hr.employee.wage.line` checks the line's `enabled` flag before computing. When `enabled = False` the rule immediately returns `0.00` without executing its logic, so downstream rules that reference it receive `0.00` rather than an error or a stale value. This lets a payroll administrator disable individual premiums or taxes per employee without modifying the structure or removing lines.

The `active` and `enabled` flags are independent and intentionally distinct:

| Field | Effect when False |
|---|---|
| `active` | Hides the line from the UI and excludes it from calculation |
| `enabled` | Keeps the line visible for audit; returns `0.00` in calculation |

Disabling a premium for audit transparency therefore uses `active = True, enabled = False`, so that the exemption is visible and demonstrably deliberate.

The enabled flag applies only to premium and tax computation rules, never to the shared income-base intermediates. The following rules always execute regardless of which premiums are enabled:

| Seq | Code | Reason |
|---|---|---|
| 20 | BVZ_PREM_INC | Base for BVZ_EMP and BVZ_ER |
| 50 | AOV_PREM_INC | Base for AOV/AWW, the surcharge, and AVBZ |
| 80 | TAX_INC | Base for LOONBEL_RAW |
| 90 | LOONBEL_RAW | Base for LOONBEL |
| 130 | NET | Final output — always required |
| 150 | TOTAL_ER_COST | Informational aggregate — always required |

A consequence worth stating explicitly: disabling AOV/AWW for an employee aged 67 does not disable `AOV_PREM_INC`, so AVBZ continues to use that base and computes correctly.

# Data Models

The module extends three standard models and introduces five new ones.

## Extensions to Standard Models

### hr.salary.rule

Extended with a `singleton` boolean (default `True`) that controls whether a wage component may be applied more than once to the same employee. Every wage component is defined here as a Tier 1 global rule.

### hr.contract

Extended with `l10n_cw_ov_percentage` (Float), the OV gevarenklasse rate fixed per employee for the duration of the contract. In the detailed design phase this interim Float is intended to be replaced by a Many2one to a dedicated `l10n_cw.svb.industry` model holding the official SVB gevarenklasse list (deferred — see roadmap).

### hr.employee

Extended with annual toeslag fields used as monetary deductions from computed tax: `l10n_cw_only_earner_deduction` (alleenverdienerstoeslag), `l10n_cw_child_deduction` (kindertoeslag, cumulative), and `l10n_cw_old_age_deduction` (ouderentoeslag).

## New Models

### hr.wage.component.set and hr.wage.component.set.line (Tier 2)

A named, company-scoped grouping of Tier 1 rules functioning as a one-time applicator template.

| Field | Type | Description |
|---|---|---|
| `component_id` | Char | Unique, immutable, indexed technical code (e.g. `STD_OFFICE`); stable reference key for reports and integrations |
| `name` | Char | Set name |
| `description` | Text | Optional description |
| `company_id` | Many2one → res.company | Company scope |
| `set_line_ids` | One2many → set.line | Component lines |

Each set line carries `set_id`, `salary_rule_id` (the referenced global rule), `sequence`, and an optional `parameter_override` default.

### hr.employee.wage.line (Tier 3)

One record per wage component per employee, fully independent after creation.

| Field | Type | Description |
|---|---|---|
| `employee_id` | Many2one → hr.employee | The employee |
| `salary_rule_id` | Many2one → hr.salary.rule | Global rule reference (read-only after creation) |
| `sequence` | Integer | Evaluation sequence |
| `active` | Boolean | Deactivate without deleting (UI visibility) |
| `enabled` | Boolean | Participation in calculation; `False` returns `0.00` (default `True`) |
| `parameter_value` | Float | Employee-specific parameter (e.g. overtime rate) |
| `salary_rule_name` | Char (related, read-only) | Mirror of `salary_rule_id.name` |
| `payslip_description` | Char | Payslip label override, editable by payroll admin |

The displayed payslip label resolves as `payslip_description or salary_rule_id.name`.

### hr.wage.component.ytd

Year-to-date accumulation per wage component per employee per calendar year. Records are created and updated automatically when a run is closed; prior-year records are retained indefinitely for historical reporting and audit.

| Field | Type | Description |
|---|---|---|
| `employee_id` | Many2one → hr.employee | The employee |
| `salary_rule_id` | Many2one → hr.salary.rule | The wage component rule |
| `wage_line_id` | Many2one → hr.employee.wage.line | The Tier 3 line |
| `year` | Integer | Calendar year |
| `company_id` | Many2one → res.company | Company scope |
| `ytd_amount` | Float | Accumulated amount for the year |
| `last_updated` | Date | Date of last update (run close date) |
| `last_payslip_id` | Many2one → hr.payslip | Last payslip that updated this record |

### hr.tax.bracket

Dated rate storage supporting all rate types via a single model.

| Field | Type | Description |
|---|---|---|
| `name` | Char | Description |
| `sequence` | Integer | Application order |
| `income_from` | Float | Band lower bound |
| `income_to` | Float | Band upper bound (0 = no ceiling) |
| `rate` | Float | Rate as a percentage |
| `valid_from` | Date | Effective date (mandatory) |
| `valid_to` | Date | Expiry date (empty = still active) |
| `tax_type` | Selection | `bijzondere_beloning` / `bvz_emp` / `bvz_er` / `avbz_emp` / `avbz_er` / `aov_aww_emp` / `aov_aww_er` / `aov_aww_surcharge` / `zv` / `ov` |
| `active` | Boolean | Active flag |

The `compute_tax(income, tax_type, date)` method selects active brackets valid on the given date, accumulates progressive tax band by band, and returns the rounded amount. It serves SVB premiums and bijzondere beloningen only. Loonbelasting is not computed via `compute_tax`; it is looked up via `hr.loonbelasting.tabel.lookup_loonbelasting` (see AD-20).

# Tax and Rate Management

## 2026 Loonbelasting Table

Applied to the periodic fiscal wage (`TAX_INC`) using the official Belastingdienst Curaçao lb-maandtabel, published annually per Ministeriële Regeling. The lb-maandtabel is the statutory instrument for loonbelasting withholding (a prepayment of inkomstenbelasting). The Schijventarief (progressive bracket table) is the annual inkomstenbelasting instrument — it is not the correct instrument for employer withholding and must not be used for loonbelasting calculation.

The lookup method: `wage_from = floor(TAX_INC / 5.00) * 5.00`; read the corresponding row from `hr.loonbelasting.tabel.lijn`. Above the table ceiling (XCG 16,670/month): `ceiling_tax + (TAX_INC − 16,670) × 46.5%` (MR 144 § Algemeen). Missing table raises `UserError` (AD-18). The 2026 maandtabel has ≈ 3,335 rows and is seeded as `data/hr.loonbelasting.tabel.lijn.csv`.

**Versioning and correction handling:** The `hr.loonbelasting.tabel` header model carries fields `name`, `period_type`, `year` (Integer), `valid_from`, `valid_to`, and `active`. Multiple versions of the same (period_type, year) are supported — the Belastingdienst occasionally publishes a corrected table mid-year. The selection rule picks the active record with the latest `valid_from ≤ payslip.date_to`; ties (same `valid_from`) are broken by `id desc` (most recently uploaded). A retroactive correction (same `valid_from` as the original) is automatically preferred for herberekening of all prior payslips in that year. A prospective correction (later `valid_from`) applies only to payslips from that date onward.

Example: TAX_INC = XCG 3,245.00 → lookup wage_from = 3,245 → loonbelasting = XCG 316.88 raw.

## 2026 Toeslagen

Applied as monetary deductions from the computed tax, not as income reductions. The basiskorting applies automatically to all employees; the rest are stored as annual amounts on employee fields.

| Toeslag | Annual Amount (XCG) | Source |
|---|---|---|
| Basiskorting | 2,915 | Automatic — all employees |
| Alleenverdienerstoeslag | 1,779 | `l10n_cw_only_earner_deduction` |
| Kindertoeslag — 1st child | 948 | `l10n_cw_child_deduction` (cumulative) |
| Kindertoeslag — 2nd child | 475 | Added to above |
| Kindertoeslag — 3rd child | 124 | Added to above |
| Kindertoeslag — 4th child+ | 96 | Added to above |
| Ouderentoeslag (standard) | 1,342 | `l10n_cw_old_age_deduction` |
| Ouderentoeslag (reduced) | 673 | Alternative value |

## 2026 Bijzondere Beloningen Rate Table

The exclusief basiskorting variant is used (basiskorting applied once, post-calculation, across both regular and bijzondere tax). The marginal rate is chosen by annual total loon and applied only to the bijzondere beloning.

| Annual Total Loon (XCG) | Rate |
|---|---|
| ≤ 43,500 | 9.75% |
| ≤ 58,000 | 15.00% |
| ≤ 86,900 | 23.00% |
| ≤ 123,100 | 37.50% |
| ≤ 181,000 | 46.50% |

## 2026 SVB Premium Rates

| Premium | Employee % | Employer % | Annual Ceiling (XCG) |
|---|---|---|---|
| AOV/AWW (combined) | 6.5% | 9.5% | 100,000 |
| AOV above ceiling (employee only) | 1.0% | — | No ceiling |
| AVBZ | 0.5% or 1.5%* | 0.5% | 606,247.08 |
| BVZ | Sliding 0%–4.3%** | 9.3% | 150,000 |
| ZV | — | 1.9% | 85,753.20 |
| OV | — | 0.5%–5.0% (by gevarenklasse) | 85,753.20 (shared with ZV) |

\* AVBZ employee 0.5% if annual AOV income < XCG 29,897.44; otherwise 1.5%.
\*\* BVZ employee 0% below XCG 12,000/year, graduating to full 4.3% above XCG 18,000/year.

## Rate Update Procedure

Rates change without code deployment. The administrator opens Salarisadministratie → Configuratie → Tarieven, sets `valid_to` on all expiring records, and creates new records with the updated `valid_from` and rates. Historical records are never deleted, because they are required to recompute prior payslips correctly.

# Payroll Run Lifecycle

The payroll run progresses through three states — CONCEPT (draft) → TE CONTROLEREN (verify) → AFGESLOTEN (close) — while individual payslips progress CONCEPT → TE CONTROLEREN → BEVESTIGD (done), with GEANNULEERD (cancel) available as a side branch before close. Recomputation (herberekening) is permitted in any state before close, so corrections can be made without reverting a posted journal entry. See Figure 3.

## On Close

Closing the run is the single point at which the system commits results. The `action_close()` method performs the following, in order:

1. Confirm all payslips in the run (status → done).
2. Lock the payslips against further editing.
3. Iterate each confirmed payslip's lines and locate or create the corresponding `hr.wage.component.ytd` record.
4. Increment `ytd_amount` by each line amount and update `last_updated` and `last_payslip_id`.
5. Generate and post the accounting journal entry (`account.move`: DRAFT → POSTED).
6. Make the run-level reports available (B-01, B-02, B-05, A-01).

After the last run of the calendar year, the year-end reports (B-03, B-04, B-06, B-07) are produced from the accumulated YTD records.

# Accounting Integration

Closing a run posts a balanced journal entry. The GL account numbers below are indicative; final numbers are configured to match the company's Chart of Accounts (deferred to v1.1R).

| Rule(s) | Side | GL (indicative) | Description |
|---|---|---|---|
| TOTAL_LOON | Debit | 6100 | Salary expense (gross incl. fringe benefits) |
| AOV_AWW_ER | Debit | 6200 | Employer AOV/AWW cost |
| AVBZ_ER | Debit | 6210 | Employer AVBZ cost |
| BVZ_ER | Debit | 6220 | Employer BVZ cost |
| ZV_ER | Debit | 6230 | Employer ZV cost |
| OV_ER | Debit | 6240 | Employer OV cost |
| NONTAXED | Debit | 6260 | Onbelaste vergoedingen (employer cost) |
| NET | Credit | 2100 | Net salary payable to employees |
| LOONBEL + EXTRA_TAX | Credit | 2200 | Loonbelasting payable to Belastingdienst CW |
| AOV_AWW_EMP + AOV_AWW_ER + AOV_AWW_1PCT | Credit | 2300 | Total AOV/AWW payable to SVB |
| AVBZ_EMP + AVBZ_ER | Credit | 2310 | Total AVBZ payable |
| BVZ_EMP + BVZ_ER | Credit | 2320 | Total BVZ payable to SVB |
| ZV_ER | Credit | 2330 | ZV payable to SVB |
| OV_ER | Credit | 2340 | OV payable to SVB |
| NONTAXED | Credit | 2350 | Onbelaste vergoedingen payable to employee |

## Balance Identity

Total debit equals salary expense plus all employer contributions plus non-taxed reimbursements. Total credit equals net payable plus all tax and premium payables plus non-taxed reimbursements. By the definition of NET (total loon = net + all employee deductions), the employer-cost debits equal the payable credits, so debit equals credit by construction.

# Reports

## A-Series — Standard Odoo 19

Available natively with `hr_payroll`; no custom development required, though some templates are customized for Curaçao layout and codes.

| Code | Report (NL) | Description | Customized |
|---|---|---|---|
| A-01 | Loonstrook | Individual payslip PDF per employee per run | Yes — Curaçao layout |
| A-02 | Salarisanalyse | Pivot: payslip count, leave days, net/gross by department | No |
| A-03 | Loonregelrapport | Payslip line detail across employees | No |
| A-04 | Gewerkte Dagen Analyse | Worked days, hours, period data per employee | No |
| A-05 | Betalingsrapport | Batch salary payment file for bank transfer | Yes — Curaçao bank format (TBD) |
| A-06 | Loonrun Overzicht | Overview of all payslips in a run | No |

## B-Series — Custom Reports

| Code | Report (NL) | Description | Data Source | Target |
|---|---|---|---|---|
| B-01 | Aangifte Loonbelasting | Monthly wage tax declaration per run | `hr.payslip.line` | v1.0R |
| B-02 | Aangifte SVB Premies | Monthly SVB premium declaration (all premiums, both shares) | `hr.payslip.line` | v1.0R |
| B-03 | Loonbelastingkaart (Jaaropgaaf) | Annual wage tax statement per employee | `hr.wage.component.ytd` | v1.1R |
| B-04 | Verzamelloonstaat CSV | Annual collective wage statement in official CSV format | `hr.wage.component.ytd` | v1.1R |
| B-05 | Salarisjournaalboeking | Balanced payroll journal entry summary per run | `account.move` | v1.0R |
| B-06 | Loonkostenrapport per Medewerker (YTD) | YTD labour cost per employee | `hr.wage.component.ytd` | v1.1R |
| B-07 | Loonkostenrapport per Afdeling (YTD) | YTD labour cost by department | `hr.wage.component.ytd` | v1.1R |
| B-08 | ZV Ziekengeld Overzicht | ZV sick pay overview per run for SVB reimbursement claim | `hr.payslip.line` | v1.1R |
| B-09 | Batch Salarisbetaling Export | Bank payment file (format per bank) | `hr.payslip` | TBD |

# Security and Access Control

The four user groups (see Users and Roles) enforce least privilege. A record rule restricts employees to their own payslips:

```xml
<record id="rule_payslip_employee_own" model="ir.rule">
    <field name="name">Employee: own payslips only</field>
    <field name="model_id" ref="hr_payroll.model_hr_payslip"/>
    <field name="groups" eval="[(4, ref('group_l10n_cw_employee'))]"/>
    <field name="domain_force">[('employee_id.user_id', '=', user.id)]</field>
</record>
```

## Data Protection

Payroll data is personal data under the Landsverordening bescherming persoonsgegevens (A.B. 2010 no. 84). The module applies least privilege via group-based access, an audit trail via `mail.thread` on all custom models, append-only tax bracket records, and no transmission of payroll data to external services.

# Configuration and Deployment

## Seed Data Installed with the Module

The `CWMONTHLY` structure type and `CWSTAFF` structure; all salary rule categories and rules (Steps 10–150); the 2026 lb-maandtabel (≈ 3,335 rows, `hr.loonbelasting.tabel` + `.lijn`); the 2026 SVB premium rates and ceilings; and the 2026 bijzondere beloningen rate records (6 correct bands).

## Per-Organization Configuration at Onboarding

The GL account mapping (mapping the indicative numbers to the company Chart of Accounts); the OV gevarenklasse percentage per contract; the toeslag fields per employee; security group assignments; the payslip distribution mechanism; and the Tier 2 component sets and their application to employees (Tier 3).

## Working Hours Normalization

Monthly hours are normalized as `(8h × 5d × 52wk) / 12 = 173.33 hrs/month`, used as the divisor to derive the hourly rate from the monthly contract wage. This assumes a standard 40-hour, five-day week.

## Module Manifest

The module is published as version `19.0.0.1.0`, category `Accounting/Localizations/Payroll`, license `OPL-1`, country `cw`, `installable` and not auto-installed.

# Open Questions and Assumptions

The following items are within scope but require explicit decisions before the affected components can be designed in detail. They do not block the v1.0R milestone unless stated.

| # | Item | Decision required | Blocks |
|---|---|---|---|
| OQ-01 | Payslip distribution method | Odoo Employee Portal, Employee App, automatic email on close, or a combination; if email, the language (Dutch / Papiamentu / English) | v1.0R onboarding |
| OQ-02 | Verwervingskosten disable option | Option A (always applied to all) vs Option B (disable-able per employee); design notes "pending confirmation" | v1.0R development |
| OQ-03 | Overtime default rates | Confirm 150/150/200/200 against Curaçao labour regulations before v1.0R sign-off | v1.0R sign-off |
| OQ-04 | Granular user-rights configuration | Menus, actions, and editable fields per group, finalized in detailed design | v1.0R detailed design |
| OQ-05 | Final GL account numbers | Company Chart of Accounts not yet finalized; §Accounting numbers are placeholders | v1.1R |
| OQ-06 | Verzamelloonstaat specification | Confirm the portal accepts the 2025+ spec; confirm Lei di Bion field values | v1.1R |
| OQ-07 | SVB gevarenklasse list | Sourcing the complete official list to replace the interim Float with `l10n_cw.svb.industry` | v1.1R |
| OQ-08 | Loan / garnishment scope | Whether balance tracking is in scope; the current statutory bestaansminimum and how it is stored | v1.1R |
| OQ-09 | ZV sick pay design | Waiting-period tracking per episode, cross-period handling, SVB reimbursement tracking, above-ceiling pay policy | v1.1R |
| OQ-10 | Batch payment format (B-09) | Curaçao bank payment file formats to be researched and confirmed | TBD |

# Acceptance Criteria

The following must hold before v1.0R is released to production.

**Calculation correctness.** For representative test employees (at minimum: a standard employee, a BVZ-exempt employee, an employee above the AOV ceiling, and an employee with a bijzondere beloning), loonbelasting and SVB premium amounts match the official 2026 publications within XCG 0.02 (rounding only).

**Balanced journal entry.** Every run close produces an `account.move` where total debit equals total credit, verified across at least ten test payslips of varying salary levels.

**Enable/disable integrity.** Disabling a premium on an employee's wage line yields `0.00` for that premium and leaves all other payslip lines and the NET amount unchanged.

**Rate update without deployment.** Setting `valid_to` on a bracket and inserting a new record produces correct tax for payslips dated after the new `valid_from`, with no code change or module upgrade.

**Access control.** A user in `group_l10n_cw_employee` can read only their own payslips and no other employee's payroll data.

**Declarations.** Reports B-01 and B-02 produce correct totals per run, matching the sum of individual payslip line amounts.

**YTD accumulation.** After a run close, each employee's `hr.wage.component.ytd` record reflects the correct running total for the calendar year.

**Structure integrity.** Running payroll on an employee with no special inputs produces a payslip with positive NET for any contract wage above the minimum threshold, with no Python errors or missing rule results.

# Release Roadmap

| Version | Contents |
|---|---|
| v1.0R | Monthly payroll engine, full statutory sequence (Steps 10–150), three-tier wage component model, loonbelasting + SVB premiums, YTD model, accounting integration, reports A-01/B-01/B-02/B-05, four user groups, Dutch UI translations |
| v1.1R | Final GL account mapping, verzamelloonstaat CSV (B-04), loonbelastingkaart (B-03), labour cost reports (B-06/B-07), ZV sick pay (B-08), loan deductions and garnishments, additional pay periods, SVB gevarenklasse dropdown |
| v1.2R | DGA payroll, beschikking multi-year tracking |
| v2.0R | Electronic filing with Belastingdienst CW, extension to Aruba/Sint Maarten, pension fund integrations |

# Authoring Assumptions

This PRD was derived from the Technical Design Document v3.0D and three architecture diagrams. Where the source was silent, ambiguous, or internally contradictory, the assumptions below were made. Each is flagged with its rationale so reviewers can confirm or override.

| # | Assumption | Rationale | Review at |
|---|---|---|---|
| A-01 | PRD scoped primarily to v1.0R, with the roadmap documented separately | The user's earlier feasibility discussion identified v1.0R-only as the lower-risk default; requirements are written for the initial release while the roadmap preserves later versions | Release Roadmap |
| A-02 | Cessantia excluded entirely, including removal of the CESSANTIA rule (Seq 160) from the sequence map and GL mapping | The user instructed "ignoring Cessantia," and the source is contradictory — Seq 160 and GL accounts 6250/2360 include it while a later section marks it permanently out of scope. Exclusion resolves the contradiction in favour of stated intent. If reinstated, Seq 160, GL accounts, and the balance formula must change together | Scope (Out of Scope) |
| A-03 | The term basiskorting is used throughout, replacing basisaftrek | The v3.0D change log explicitly corrects this; a stale "Basisaftrek" comment remaining in the LOONBEL rule code is treated as a non-authoritative artefact | Toeslagen table |
| A-04 | The exclusief basiskorting variant of the bijzondere beloningen table is used | The source confirms this explicitly with rationale (single post-calculation deduction, avoiding double deduction); treated as confirmed, not an open question | Bijzondere Beloningen table |
| A-05 | Overtime default rates (150/150/200/200) are indicative, not confirmed | The source labels them indicative and requires confirmation against Curaçao labour regulations before v1.0R; captured as OQ-03 | OQ-03 |
| A-06 | The verwervingskosten forfeit is applied automatically to all employees (Option A) | The source applies it unconditionally in code and marks only the disable option as pending; Option A is the statutory baseline. Option B would be an exception mechanism raised as a change request | OQ-02 |
| A-07 | GL account numbers are indicative placeholders, not requirements | The source states the numbers are indicative and lists final GL mapping as a v1.1R item; included to illustrate the debit/credit structure only | Accounting Integration, OQ-05 |
| A-08 | The 2025+ verzamelloonstaat specification is the primary target, pre-2025 retained for reference | Stated directly in the source; assumes portal confirmation before v1.1R implementation (OQ-06) | OQ-06 |
| A-09 | Working-hours normalization at 173.33 hrs/month is a fixed constant | Derived from a standard 40h/5d week; a different standard week would require revisiting the divisor. Holds for v1.0R standard contracts | Working Hours Normalization |
| A-10 | B-05 (journal entry summary) is a v1.0R deliverable | The source lists it without a version; since accounting integration is v1.0R and the journal entry is its central output, the printed summary belongs in the same release. If wrong, it moves to v1.1R | Reports |

# Referenced Documents and Figures

| Reference | Description |
|---|---|
| Technical Design Document v3.0D | Full implementation specification (source for this PRD) |
| Figure 1 | Module Dependency Architecture — `figure-01-module-dependency-architecture.drawio.png` |
| Figure 2 | Three-Tier Wage Component Model — `figure-02-three-tier-wage-component-model.drawio.png` |
| Figure 3 | Payroll Run Lifecycle — `figure-03-payroll-run-lifecycle.drawio.png` |
| Belastingdienst Curaçao — lb-maandtabel 2026 | Official loonbelasting withholding table (statutory instrument for employer withholding) |
| Belastingdienst Curaçao — MR 144 (Ministeriële Regeling loonbelastingtabellen 2025) | Statutory basis for lb-tabel lookup method and above-ceiling formula |
| Belastingdienst Curaçao — Schijventarief 2026 | Annual inkomstenbelasting bracket table (reference only — not used for employer withholding) |
| SVB Curaçao — Official rates publication 2026 | Source for AOV/AWW, AVBZ, BVZ, ZV, OV rates and ceilings |
| Landsverordening bescherming persoonsgegevens (A.B. 2010 no. 84) | Data protection compliance basis |
| Cessantialandsverordening | Basis for permanent Cessantia exclusion |
