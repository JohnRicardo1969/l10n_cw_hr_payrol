::: {custom-style="Title"}
l10n_cw_hr_payroll
:::
::: {custom-style="Subtitle"}
Product Requirements Document — Curaçao Payroll Localization for Odoo 19 Enterprise
:::

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

Both approaches carry material risk. Manual processing is error-prone and labour-intensive, and reconciling externally calculated payroll back into the Odoo general ledger introduces a class of posting errors that are difficult to audit. Generic salary rules silently produce incorrect statutory amounts — for example, applying the wrong instrument for loonbelasting withholding, mishandling the above-ceiling AOV surcharge, using a stale basiskorting, or treating toeslagen as income reductions rather than as monetary deductions from the computed tax.

The module eliminates this gap by implementing the complete Curaçao statutory payroll framework inside Odoo, with all logic, rates, and rules derived from the official publications of the Belastingdienst Curaçao and the SVB.

# Goals and Objectives

## Primary Goals

The module is built to satisfy five primary goals.

**Statutory correctness.** Payroll calculations are correct under the current Landsverordening for loonbelasting and all SVB premiums, including the flat premium rates, ceilings, and the above-ceiling AOV surcharge, all sourced from the official Belastingdienst and SVB publications.

**Auditability.** Every calculation step is traceable. Intermediate values are materialized as salary rules, rates are stored as inspectable data records, and all custom models carry a chatter audit trail.

**Operational independence.** Payroll administrators run monthly payroll end to end inside Odoo, without any external payroll service or spreadsheet.

**Regulatory agility.** Rate changes — annual or ad hoc — require no code deployment. They are applied by creating new dated bracket records, leaving historical records intact for accurate recomputation of prior periods.

**Accounting integration.** Closing a payroll run automatically posts a balanced journal entry to the general ledger, with correct debit/credit mapping for every cost and liability account, such that total debit equals total credit by construction.

## Success Measures

The goals above are considered met when the acceptance criteria are satisfied: calculation output reconciles to the official rate publications within rounding tolerance, every run close produces a balanced journal entry, statutory exemptions can be applied per employee without breaking the calculation chain, and rates can be updated without a code release.

# Scope

## In Scope (v1.0R)

The initial production release covers monthly payroll for standard staff contracts. It includes the complete statutory calculation sequence (gross through net and total employer cost), the three-tier wage component model, the per-employee enable/disable mechanism for premiums and taxes, year-to-date accumulation, accounting integration with automatic journal posting, the four overtime types, the monthly wage tax and SVB premium declarations, the payslip PDF, and the four security roles.

The release also includes the following wage-line, earning, deduction and premium functions (decided 2026-10-08 by the PO, "Confirmed for v1.0", superseding the earlier v1.0R scope that held recurring items as monthly payslip inputs and deferred loans and garnishments):

- Employee-level dated wage lines, edited in place, with validity dates, amount basis (annual ÷ 12 or per period), recurring or one-time, and a show-on-payslip switch (AD-25).
- A generic taxable earning per employee, with an "Include in SVB wage" flag that affects ZV and OV only.
- Calculation settings for calculated amounts: basis, factor, included items, base amount, and caps per period, per year and lifetime (AD-26).
- Beschikkingsaftrek as employee-level wage lines that lower the taxable wage only.
- One untaxed-earning concept (art. 6F lid 1 LLB), replacing the former separate non-taxed reimbursement rule (AD-27).
- Net deductions (garnishment, loan or advance repayment, union dues, savings, insurance) with priority, threshold, caps, balance and a creditor per line (AD-28).
- Automatic net carry-over when net pay would be negative (AD-29).
- A generic "Correct from [date]" function that books differences as correction lines on the current payslip (AD-30).
- Year closing: last run of the year, year lock and year-end actions (AD-29).
- AOV/AWW and AVBZ with a strict monthly maximum.
- The BVZ redesign: AOV-insured status, supplement type and per-year exemption on the employee, supplement and total premium on the payslip, and a running-total ceiling (AD-24 rewritten). The optional retroactive annual recalculation is removed; past-dated changes go through "Correct from [date]" (decided 2026-10-09, superseding the per-employee Retroactive switch, OQ-19).

## Out of Scope (v1.0R)

The following are explicitly excluded from the initial release. Items with a target version are deferred (see the release roadmap); Cessantia is a permanent exclusion. Loan deductions and wage garnishments are no longer listed here: they are in v1.0R as net deductions (decided 2026-10-08, superseding their v1.1R deferral).

| Excluded item | Reason | Target |
|---|---|---|
| Bi-weekly, semi-monthly, weekly payroll | v1.0R is monthly only; other periods need separate tax tables and divisors | v1.1R |
| ZV sick pay processing | Requires decisions on waiting-period tracking and SVB reimbursement, plus `hr_holidays` integration | v1.1R |
| Statutory vacation accrual & balance (Vakantieregeling 1949) | Leave management built on native `hr_holidays`; full design in `docs/design/cw-vacation-accrual-v1.1R.md` | v1.1R |
| Bank payments / bank interface for net-deduction creditors | Routing net deductions to the creditor's bank account (`res.partner.bank`); decided 2026-10-08 | v1.1R |
| Loonbelastingkaart categories for untaxed earnings | Category per untaxed-earning line; decided 2026-10-08 | v1.1R |
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

Direct dependencies declared in `__manifest__.py` are `hr`, `hr_holidays`, `hr_payroll`, `hr_payroll_account`, and `hr_attendance`. (`hr_contract` was dropped 2026-07-07: the module no longer exists in Odoo 19 — contracts are absorbed into core `hr` as the `hr.version` model.) Odoo resolves the transitive dependencies automatically: `resource` (drives working-hour normalization and absence handling), `mail` (provides `mail.thread` and `mail.activity.mixin` for chatter and audit trails), and `account` (provides `account.account`, `account.journal`, and `account.move`).

The full installation order is:

```
base → mail → resource → hr → hr_holidays
→ hr_attendance → account → hr_payroll → hr_payroll_account
→ l10n_cw_hr_payroll
```

# Users and Roles

Four user roles are supported. Role-to-user assignment is a per-organization configuration decision made during onboarding (see Open Questions).

| Role | Odoo Group | Capabilities |
|---|---|---|
| Employee | `group_l10n_cw_employee` | View and download own final (validated or paid) payslips only |
| Payroll User | `group_l10n_cw_payroll_user` | Compute runs, edit employee wage lines and payslip descriptions, read tax brackets. Includes Odoo's Payroll Officer role, which also lets the user manage employee records |
| Payroll Manager | `group_l10n_cw_payroll_manager` | All rights of the Payroll User (the groups are laddered: Payroll Manager implies Payroll User; recorded 2026-10-09 from Tech Design v5.0D), plus full access including tax bracket management, reopening closed runs of an unlocked year (a locked year cannot be reopened in the module; decided 2026-10-08, superseding unrestricted reopening of closed runs), and entering and approving the annual Lei di Bion approval record (decided 2026-10-08). Includes Payroll User and Odoo's Payroll Administrator role (full HR administration) |
| Accountant | `group_l10n_cw_accountant` | Read payroll runs, payslips and journal entries (includes Accounting read-only access); no write access to computation |

*Decided 2026-10-06 by the PO, widening the original matrix:* Odoo binds all core payroll access to its own Payroll Officer and Payroll Administrator groups, so the Payroll User and Payroll Manager roles include them, with the HR rights those groups carry; the Accountant reads every payslip because a run is made of payslips. The roles are assigned as one choice per user (Settings → Users → "Salarisadministratie Curaçao").

*Decided 2026-10-06 by the PO (Story 1.3 review):* employees see only their own **final** payslips (state `validated` or `paid`), never drafts. Story 1.3 delivers the access rules only; usable viewing and download for Employee and Accountant (read access to payslip lines, worked days and inputs, a menu to reach payslips, and a PDF download that works for these roles) is delivered by Stories 3.6 (distribution) and 4.1 (payslip PDF).

The Employee group is intended for staff with internal Odoo user access. Portal-only employees are handled separately through the payslip distribution mechanism (see Open Questions).

# User Stories

## Employee

As an employee, I want to view and download my monthly payslip (loonstrook) as a PDF, so that I have a record of my earnings, deductions, and net pay.

## Payroll User

As a payroll user, I want to enter the per-period inputs (overtime hours, bijzondere beloningen, employee pension contribution `PENSION_EMP`) before running payroll, so that each payslip reflects that employee's actual situation for the period.

As a payroll user, I want to set up recurring employee items once as dated wage lines (Bijtelling such as company car, mobile phone and internet; generic earnings; untaxed earnings; beschikkingsaftrek; net deductions) and edit them in place when something changes, so that I do not re-enter them every month. *(Decided 2026-10-08, superseding the single "monthly inputs" story that listed fringe benefits and beschikking as monthly payslip inputs.)*

As a payroll user, I want to correct closed periods from an effective date ("Correct from [date]"), so that the difference between the correct and the withheld premium or tax is settled as identifiable correction lines on the current payslip without changing closed payslips. *(Decided 2026-10-08.)*

As a payroll user, I want to compute payroll for all employees in a run with a single action, so that I do not process payslips individually.

As a payroll user, I want to review computed payslips in a verify state before closing the run, so that I can correct errors before any journal entry is posted.

As a payroll user, I want to disable a specific premium or tax for an individual employee — for example BVZ for someone with approved private health insurance — without removing the rule from the structure, so that the exemption remains visible to auditors.

As a payroll user, I want overtime earnings (weekday, Saturday, Sunday, public holiday) to appear as separate named lines on the payslip, so that the basis for each amount is transparent.

## Payroll Manager

As a payroll manager, I want to update statutory rates by creating new dated bracket records, without writing or deploying code, so that rate changes take effect for the correct periods immediately.

As a payroll manager, I want to apply a wage component template set to one or more employees at onboarding, so that each employee starts with the correct components without line-by-line setup.

As a payroll manager, I want year-to-date totals per wage component per employee to accumulate automatically on every run close, so that annual declarations need no manual aggregation.

As a payroll manager, I want to mark a run as the last run of the year when closing it, with a confirmation that reminds me to make an Odoo.sh backup first, so that the year is locked and the year-end actions run in one controlled step, and a later correction of that year remains possible by restoring the backup. *(Decided 2026-10-08; backup reminder decided 2026-10-08, superseding a year close that a controlled reopen could undo.)*

As a payroll manager, I want to record the employer's annual Lei di Bion approval (request, status, beschikking and the employees covered with their estimated overtime hours and prior-year wage) once per calendar year, so that exempt overtime is applied only to covered employees and the approval is auditable. *(Decided 2026-10-08, superseding an approval held as a beschikking field on the employee.)*

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
| `version` | `hr.version` record (Odoo 19 successor of the v3.0D `contract`/`hr.contract`; the localdict exposes `version`, not `contract`) |
| `payslip` | `hr.payslip` record |
| `worked_days` | Dict of worked-days lines keyed by code (Odoo 19 — plain dict, no attribute access; e.g. `worked_days['WORK100'].number_of_hours`, guard membership first) |
| `inputs` | Dict of payslip input lines keyed by code (Odoo 19 — plain dict, no attribute access; guard absent inputs: `inputs['PENSION_EMP'].amount if 'PENSION_EMP' in inputs else 0.0`) |
| `categories` | Accumulated category totals (e.g. `categories.BASIC`, `categories.ALW`, `categories.DED`, `categories.ER`) |
| `rules` | Prior rule results (e.g. `rules.BVZ_PREM_INC.amount`) |
| `env` | Odoo environment for ORM queries (e.g. `env['hr.tax.bracket'].search(...)`) |
| `result` | The computed amount for this rule — must be assigned |

By convention, deduction rules return negative values, so that the NET rule can sum categories directly.

## Canonical Sequence Map

The complete v1.0R sequence (Cessantia excluded — see Authoring Assumptions) is below. *(Decided 2026-10-08, superseding the earlier map: `EARNING` (15) and `UNTAXED_EARN` (16) are added; `BVZ_SUPPL` (30) and `BVZ_TOTAL` (40) replace `BVZ_ER` and `BVZ_EMP`; `NET_PRE` (125), `NET_DED` (126) and `NET_CARRY` (128) are added before `NET`; the separate `NONTAXED` rule (formerly Seq 140) is removed; AOV/AWW and AVBZ use a monthly maximum.)* *(Decided 2026-10-09, superseding the separate `BVZ_SUPPL_EXTRA` line at Seq 31: with OQ-14 resolved, `BVZ_SUPPL` holds the whole supplement, also under type `full`, and Seq 31 is removed.)* *(Decided 2026-10-09, superseding the open OQ-20: the Bijtelling offset is added at Seq 127.)* Correction lines from "Correct from [date]" take the category of the corrected rule and a `CORR_*` code; the exact codes are left to the implementing story.

| Seq | Code | Pseudocode Step | Description | On Payslip |
|---|---|---|---|---|
| 10 | TOTAL_LOON | Step 1 | Contract wage + Bijtelling wage lines (wage in kind; each Bijtelling line shown as its own payslip line) | Yes |
| 11 | OVT_WD | Step 1 | Weekday overtime (configurable rate, default 150%) | Yes |
| 12 | OVT_SAT | Step 1 | Saturday overtime (configurable rate, default 150%) | Yes |
| 13 | OVT_SUN | Step 1 | Sunday overtime (configurable rate, default 200%) | Yes |
| 14 | OVT_PH | Step 1 | Public holiday overtime (configurable rate, default 200%) | Yes |
| 15 | EARNING | Step 1 | Generic taxable earning (`ALW`, employee wage lines) | Per line (show-on-payslip switch) |
| 16 | UNTAXED_EARN | Step 1 | Untaxed earning (`ALW`, flagged `is_untaxed`, art. 6F lid 1 LLB) | Per line (show-on-payslip switch) |
| 20 | BVZ_PREM_INC | Step 2 | BVZ premium income base (excludes untaxed earnings) | No |
| 30 | BVZ_SUPPL | Step 3 | BVZ employer supplement, paid to the employee ("+" line, `ALW` flagged `is_untaxed`, not wage under art. 6F lid 1 sub l LLB; the whole supplement, including type `full`) | Yes |
| 40 | BVZ_TOTAL | Step 4 | BVZ total premium ("−" line, `DED`), running total up to the pro-rated ceiling | Yes |
| 50 | AOV_PREM_INC | Step 5 | AOV/AWW/AVBZ premium income base (excludes untaxed earnings) | No |
| 60 | AOV_AWW_EMP | Step 6 | AOV/AWW employee 6.5% (up to monthly maximum) | Yes |
| 61 | AOV_AWW_ER | Step 6 | AOV/AWW employer 9.5% (up to monthly maximum) | Yes |
| 62 | AOV_AWW_1PCT | Step 6 | AOV employee surcharge 1% above the monthly maximum | Yes |
| 70 | AVBZ_EMP | Step 7 | AVBZ employee flat 1.5% (up to monthly maximum) | Yes |
| 71 | AVBZ_ER | Step 7 | AVBZ employer 0.5% (up to monthly maximum) | Yes |
| 80 | TAX_INC | Step 8 | Fiscal wage base for loonbelasting (also subtracts beschikkingsaftrek lines and untaxed earnings) | No |
| 90 | LOONBEL_RAW | Step 9 | Raw loonbelasting from lb-maandtabel | No |
| 100 | LOONBEL | Step 10 | Loonbelasting after toeslagen deduction | Yes |
| 110 | EXTRA_TAX | Step 11 | Tax on bijzondere beloningen (separate table) | Yes |
| 120 | ZV_ER | Step 12 | ZV employer 1.9% (up to ZV/OV ceiling) | Yes |
| 121 | OV_ER | Step 12 | OV employer variable % (up to ZV/OV ceiling) | Yes |
| 125 | NET_PRE | Step 13 | Net before net deductions (base for percentage net deductions) | No |
| 126 | NET_DED | Step 13 | Net deductions (`DED`, employee wage lines) | Yes |
| 127 | (code set by Story 2.11) | Step 13 | Bijtelling offset: wage in kind deducted again from net ("−" line, `DED`, negative; never gated) | Yes |
| 128 | NET_CARRY | Step 13 | Net carry-over in (from the previous payroll) and out (shortfall to the next) | Yes |
| 130 | NET | Step 13 | Net salary payable to employee | Yes |
| 150 | TOTAL_ER_COST | Step 14 | Total employer cost, including the BVZ supplement `BVZ_SUPPL` (informational) | No |

## Step Design Detail

This section describes the intended computation of each step. Ceiling handling (decided 2026-10-08, superseding the 2026-07-08 AD-24 rule that computed AOV/AWW, BVZ and AVBZ cumulatively against their annual ceilings): **AOV/AWW, AVBZ, ZV and OV use a monthly maximum** applied to each period on its own, and **AD-24 now applies to BVZ only**, as a running total up to a pro-rated ceiling (Steps 3–4). The shared premium bases stay uncapped. The period-specific lb-maandtabel is applied directly; no rule annualises.

### Step 1 — Total Loon, Overtime and Earnings (Seq 10–16)

`TOTAL_LOON` is the anchor for all downstream calculations: contract wage plus the employee's Bijtelling wage lines (natura-loon such as company car, mobile phone and internet; non-singleton). *(Decided 2026-10-08, superseding the `FRINGE_BENEFITS` payslip input: Bijtelling moved from a monthly payslip input to employee-level wage lines.)* Bijtelling is wage **in kind**: it is in gross, `TAX_INC` and the premium bases, but it is not paid in cash, so it must not raise cash net pay; a matching non-cash offset applies. Bijtelling stays inside `TOTAL_LOON` (category `BASIC`), with each Bijtelling line shown as its own payslip line; after tax and premiums the same amount is deducted again in the net block by the Bijtelling offset (Seq 127, a negative `DED` line, code set by Story 2.11), so the employee pays only the tax and premiums on it. The offset is never gated: disabling it would pay wage in kind out as cash. NET, the AD-14 bases and `TAX_INC` are unchanged *(decided 2026-10-09, superseding the open OQ-20 "offset line or separate category")*.

The four overtime rules each compute their amount from the corresponding hours input (`OVT_WD_HRS`, `OVT_SAT_HRS`, `OVT_SUN_HRS`, `OVT_PH_HRS`) and the rate stored on the employee's wage line as `parameter_value`, deriving the hourly rate from the contract wage divided by the normalized monthly hours. Overtime contributes to the ALW category alongside other allowances. Overtime pay never enters the ZV/OV base (see Step 12; decided 2026-10-08, superseding AD-14's "overtime included" as far as it applied to ZV and OV). An employee with no overtime simply has zero hours entered and the rules evaluate to zero without error. The overtime hours, bijzondere beloningen and `PENSION_EMP` remain per-period payslip inputs.

**Employee-level dated wage lines (AD-25; decided 2026-10-08, superseding monthly payslip inputs for recurring items).** Recurring per-employee items are set up once on the Tier-3 wage line and edited in place when something changes; there is no version history in the module (history is the closed payslips; older states come from the Odoo.sh backup). Each line has a validity window (`date_from` / `date_to`), an amount, an amount basis (annual amount ÷ 12 per monthly period, or amount per period), recurring or one-time (a one-time line resets to 0 at run close), and a show-on-payslip switch (hidden lines still count in every calculation). The payroll reads the line as it is at the moment of calculation; the dates only decide whether the line applies to the payslip period. A mistake found before close is fixed by editing the line and recalculating (herberekening). Edit a line for a new period only after the previous period's run is closed, otherwise a recalculation of the still-open run uses the new values. Multiplicity follows the `singleton` flag on the salary rule.

**Generic taxable earning — `EARNING`, Seq 15 (decided 2026-10-08).** An employee-level, non-singleton, taxable earning in `ALW`. Per line: a flat amount or a calculated amount (see Calculation settings below); recurring or one-time; validity dates; year-to-date amount shown; show-on-payslip switch. The per-line flag **Include in SVB wage** (default on) affects **ZV and OV only**; AOV/AWW, BVZ and AVBZ always follow the taxable wage, so the flag never removes an earning from those bases. Typical cases for switching it off are ZV/OV benefits paid through the employer and severance; verify with the SVB before switching it off. A line may be flagged as taxed as a bijzondere beloning (the existing `is_bijzondere_beloning` route, AD-21); otherwise it is taxed via the maandtabel.

**Untaxed earning — `UNTAXED_EARN`, Seq 16 (AD-27; decided 2026-10-08, superseding the separate `NONTAXED` rule formerly at Seq 140).** Untaxed earnings are wage components that under art. 6F lid 1 LLB do not count as wage (for example ziektekostenvergoeding under sub n, expense allowances under sub o, gifts up to Cg 250 per year under sub r, employer premium supplements under sub l). They are part of gross and of net pay (the amount paid out equals net), but they are **excluded from `TAX_INC` and from the AOV/AWW, BVZ and AVBZ premium bases**, the same exclusion pattern as Lei di Bion exempt overtime (AD-23). ZV/OV inclusion follows the per-line "Include in SVB wage" flag, which defaults to off for untaxed earnings. They are modelled as `ALW` earnings carrying an `is_untaxed` (6F) flag, not as a separate category, so NET = BASIC + ALW + DED still holds and the premium and tax bases subtract the flagged earnings. Per line: the **legal ground** (art. 6F lid 1 sub …, e.g. "6F-1-n ziektekosten") for audit; an amount per period with an optional multiplier; a one-time option (resets to 0 at run close); show-on-payslip; non-singleton; validity dates. Expense reimbursements are untaxed earnings. The Loonbelastingkaart category per line is deferred to v1.1R.

TODO(nroosje, 2026-10-08): double-check the merge of untaxed earnings and the former NONTAXED reimbursement line, and correct it if needed - merged on the PO's instruction pending review.

**Calculation settings for calculated amounts (AD-26; decided 2026-10-08).** One shared mechanism serves the generic taxable earning, the untaxed earning and the percentage part of a net deduction. Settings per wage line:

- **Basis**: amounts (the sum of selected **included items**, which are results of other salary rules and must have a lower sequence, AD-3) or **hours**.
- **Factor**: a percentage, an hourly rate or a multiplier. The hourly rate is the employee's hourly wage, either **standard** (contract wage ÷ 173.33) or **SVB-wage based**: (base wage + fixed allowances + commissions + the monthly reserve for fixed periodic payments such as vakantiegeld or a 13th month) ÷ 173.33. The reserve is annual amount ÷ 12 of each earning line flagged "vaste periodieke uitkering"; incidental overtime never counts in the SVB wage. The SVB-wage rate is higher, and so is any overtime pay based on it *(decided 2026-10-09, superseding the open OQ-13; mechanism detail in Story 1.11)*. Choosing multiplier fixes the multiplier switch to Yes; a multiplier may also be stored without being used.
- **Include base wage**: adds the contractual wage `version.wage` (not this month's actual `BASIC` result).
- **Base amount**: a fixed amount added to the basis (for example base amount 250 × 100% gives a fixed allowance of 250).
- **Caps**, in order: maximum per period, maximum per calendar year (year-to-date), and a **cumulative (lifetime) maximum**; once the lifetime maximum is reached, the line stops producing an amount permanently. The lifetime cap needs a running total per wage line across years, held in a lifetime accumulator that is updated only at run close (AD-9).

The formula is `basis = (version.wage if include_base_wage else 0) + Σ included items + base_amount` (or hours), `result = basis × factor`, then the caps per period, per year and lifetime.

### Step 2 — BVZ Premium Income Base (Seq 20)

The BVZ base derives from `categories.BASIC + categories.ALW` (overtime included) per **AD-14**, less the earnings flagged `is_untaxed` (decided 2026-10-08, superseding the base that included every `ALW` earning) — the verwervingskosten forfeit is **not** deducted here (AD-14 moves it to `TAX_INC` only). The base itself is **uncapped**; the ceiling is applied in the premium rules (Steps 3–4) using the BVZ running total of **AD-24** (rewritten 2026-10-08, superseding the cumulative method against the full annual ceiling). This rule is a shared intermediate and always executes. *(Resolved — F1: per the Landsverordening BVZ (P.B. 2013, no. 3) Art. 1.1(o) → Landsverordening inkomstenbelasting 1943 Art. 3(4), the BVZ premiegrondslag is the* zuivere opbrengst van arbeid *before persoonlijke aftrekposten, so the employee pension premium is **not** deducted here — confirming the AD-14 base. See `implementation-readiness-report-2026-07-04.md` F1.)*

### Steps 3–4 — BVZ Supplement and Total Premium (Seq 30, 40)

*(Decided 2026-10-08, superseding the employer 9.3% `BVZ_ER` line in category `ER` and the employee 4.3% `BVZ_EMP` deduction.)* The whole BVZ premium is legally the employee's premium. The payslip shows the employer **supplement** as a "+" line (`BVZ_SUPPL`, paid to the employee as an untaxed earning) and the **total premium** as a "−" line (`BVZ_TOTAL`, category `DED`, negative). The net effect is that the employee bears only their own share. The supplement leaves category `ER` and sits inside NET; `TOTAL_ER_COST` still includes it because it is an employer cost. The supplement is not wage under art. 6F lid 1 sub l LLB: it is untaxed and outside every premium base (AOV/AWW, BVZ, AVBZ, ZV/OV), also under supplement type `full`; the `is_untaxed` flag on `BVZ_SUPPL` follows from the law, not from a provisional choice. `BVZ_SUPPL` holds the whole supplement: the statutory 9.3% or 2.8%, the full premium under type `full`, or 0 under `none` (decided 2026-10-09, superseding the separate `BVZ_SUPPL_EXTRA` line for the part above the statutory supplement under type `full`, pending OQ-14).

**Employee fields (store facts, not percentages).**

- **AOV-insured**: stored once per employee and **date-effective** (for example it stops at 65 mid-year and applies from that date). It drives the BVZ rate (insured: 13.6%; not insured: 6.5%) and the AOV/AWW liability; AOV/AWW have their own override.
- **BVZ supplement type**: `statutory` (derived, never entered by hand: 9.3% when AOV-insured, 2.8% when not), `full` (100% of the applicable rate; the employee pays 0), or `none` (allowed only without a current employment, for example a pension from a former employer; validated against the contract type; never for a DGA).
- **BVZ exempt**: a **per-year** switch that overrides both fields (the existing `enabled` gate, set per tax year).

The four usual situations map as follows: Normal = insured + statutory (13.6% / 9.3%); Pension = not insured + none (6.5% / no supplement); Employed pension = not insured + statutory (6.5% / 2.8%); Early retiree under 65 = insured + none (13.6% / no supplement). Rates are data (AD-5/AD-22), read from the per-year `hr.svb.parameters` record, which gains the pensioner supplement (2.8%) next to the pensioner rate (6.5%).

**Running total up to a pro-rated ceiling (AD-24, BVZ only).**

- Base this period = min(premie-loon so far this year including this period, pro-rated ceiling) − premium base already used in earlier periods. The base already used is the period-bounded sum of a hidden, summable per-period **counted BVZ base** line on each confirmed payslip — never derived from the uncapped `BVZ_PREM_INC` and never as premium ÷ rate (decided 2026-10-08; code left to Story 2.3).
- Pro-rated ceiling = 150,000 × (months since the start of insurance or employment in this year, including this one) ÷ 12. The room starts at the insurance or employment start, not on 1 January (Landsbesluit BVZ art. 4 lid 3).
- Premium this period = base this period × **this period's** rate; supplement = base this period × this period's supplement rate. The calculation is segment-wise: a mid-year rate change never re-rates earlier months, so there is no negative premium in the change month.
- Rate and supplement may change within a tax year (a mid-year AOV-insured change is supported); only the BVZ exemption is fixed per year (decided 2026-10-08, superseding the rule that rate and supplement were fixed once within a tax year).
- The herberekening forward cascade (recompute later confirmed periods in ascending order) applies to BVZ only.
- Reads are period-bounded sums of confirmed lines (`date_to < this payslip.date_to`), never the annual YTD scalar and never premium ÷ rate.

For BVZ the running total is a **design choice**, not a legal requirement: BVZ is also levied over the zuiver voljaarsloon (art. 6.8 lid 3), so a monthly maximum would also be defensible. It is kept because the year total and the supplement are right immediately. The Belastingdienst and the SVB accept a monthly return on either the periodic or the cumulated limit in practice; the final annual settlement runs through the verzamelloonstaat and the employee's income-tax assessment *(decided 2026-10-09, superseding the open OQ-18 and its fallback of a company-level BVZ monthly maximum, which is dropped)*.

The BVZ low-income reduction (Landsbesluit art. 2 lid 3–4) is not applied in payroll. Withholding follows the SVB table. Any reduction is settled through the employee's annual assessment (Lv BVZ art. 6.7). The employer supplement is not corrected when the assessment later lowers the premium: it must be *at least* 9.3%, and a slightly higher supplement is allowed.

**No BVZ retroactive switch** *(decided 2026-10-09, superseding the per-employee "Retroactive" switch and the BVZ-specific retroactive annual recalculation; OQ-19)*. A change with an effective date in the past (expected annual wage, AOV-insured status, supplement type, rate) is settled over earlier months only through "Correct from [date]" (see Corrections), which asks the user when such a change is saved. A locked year is never recalculated. The system flags the 65th birthday from the date of birth and suggests AOV-insured = no from that date; the payroll user confirms with one click, and the BVZ rate follows the same date *(decided 2026-10-09, superseding the optional enhancement without an acceptance criterion; open: OQ-25)*.

### Step 5 — AOV/AWW/AVBZ Premium Income Base (Seq 50)

The AOV base derives from `categories.BASIC + categories.ALW` (overtime included) per **AD-14**, less the earnings flagged `is_untaxed`, including the BVZ supplement (decided 2026-10-08, superseding the base that included every `ALW` earning) — the shared base for AOV/AWW, the above-ceiling surcharge, and AVBZ — and always executes. The base itself is **uncapped** (the 1% surcharge, Seq 62, needs the excess above the monthly maximum); each premium rule applies its own monthly maximum. The hidden base line stays for reporting and the annual statement. Under AD-14 the verwervingskosten forfeit is not deducted here (it touches `TAX_INC` only). The beschikkingsaftrek does not reduce the premium base either: it is held as employee-level wage lines that lower `TAX_INC` only (decided 2026-10-08, superseding the single beschikking field on the employee); the Lei di Bion exemption follows AD-23 and applies only when all three exemption conditions hold (see Lei di Bion exempt overtime under 2026 SVB Premium Rates; decided 2026-10-08). *(Resolved — F1: by the same reasoning as BVZ (premiegrondslag =* zuivere opbrengst van arbeid *before persoonlijke aftrekposten), the employee pension premium (werknemersdeel) is **not** deducted from the AOV/AWW base either — the base is settled; verifying the citation under the Landsverordening AOV/AWW itself is a non-blocking documentation follow-up. See `implementation-readiness-report-2026-07-04.md` F1.)*

### Step 6 — AOV/AWW (Seq 60, 61, 62)

AOV and AWW are modeled as one combined premium. *(Decided 2026-10-08, superseding the cumulative annual-ceiling method of AD-24 for AOV/AWW.)* The employee pays 6.5% (AOV 6% + AWW 0.5%) and the employer 9.5% (AOV 9% + AWW 0.5%) on the base up to a **monthly maximum** of 100,000 ÷ 12 = XCG 8,333.33 (Gezamenlijke beschikking AOV/AWW en loonbelasting art. 6 lid 2). Each month stands alone: there is no running total, and reopening a month does not cascade into later months for AOV/AWW. For income above the monthly maximum, the employee pays an additional 1% surcharge (`AOV_AWW_1PCT`) on the excess above the **monthly** maximum only. The surcharge is zero for most employees and ensures compliance with the Landsverordening for high earners. Differences (for example income below the annual ceiling with a large bonus month, where the surcharge hits part of the bonus) are settled through the employee's annual assessment (AOV art. 29–30); this is correct by law. Part-year insurance pro-rata (AOV art. 26 lid 3) is applied in the assessment, not in payroll. AOV/AWW liability follows the employee's AOV-insured status, with its own AOV/AWW override (for example AWW art. 26 lid 2 sub b). A bonus taxed via the bijzondere table gets no own AOV/AWW premium room: the maximum applies per pay period (Gezamenlijke beschikking AOV/AWW en loonbelasting 1976, art. 6 lid 2) and the bonus belongs to the wage of the month in which it is paid (LLB art. 8 lid 6) (OQ-16). The 1% above the monthly maximum is the employee's own premium (Lv AOV art. 26 lid 3); the employer's toeslag (Lv AOV art. 58) does not cover it, and the employer pays no surcharge (OQ-17). *(Decided 2026-10-09, superseding the open OQ-16 and OQ-17.)*

### Step 7 — AVBZ (Seq 70, 71)

AVBZ uses the AOV base up to a **monthly maximum** of 606,247.08 ÷ 12 = XCG 50,520.59 (zuiver voljaarsloon, Lv AVBZ art. 22 lid 3), with no running total and no cascade; differences are settled through the assessment (art. 20 lid 2) (decided 2026-10-08, superseding the cumulative annual-ceiling method of AD-24 for AVBZ). Per the official SVB-Tabel-2026 the employee rate is a **flat 1.5%** and the employer rate a flat 0.5% — there is no low-income threshold (the earlier "0.5%/1.5% at XCG 29,897.44" is dropped, AD-5/AD-22; 29,897.44 was in fact the prior-year basiskorting breakpoint). Rates and ceiling are read from the per-year `hr.svb.parameters` record.

### Steps 8–10 — Loonbelasting (Seq 80, 90, 100)

`TAX_INC` is the fiscal wage: the AD-14 earnings base (`categories.BASIC + categories.ALW`, excluding earnings flagged `is_bijzondere_beloning`, `is_lei_di_bion_exempt` or `is_untaxed`; the Lei di Bion flag applies only when all three exemption conditions of AD-23 hold, decided 2026-10-08) less the verwervingskosten forfeit, the absolute AOV/AWW employee premium, the employee pension premium (payslip input `PENSION_EMP`, read guarded — see Python Computation Context), and the beschikkingsaftrek wage lines (decided 2026-10-08, superseding a base that did not exclude untaxed earnings and a beschikking held on the employee). The pension premium is a loonbelasting aftrekpost applied here **only** — not to the SVB premie-loon (F1, in scope for v1.0R, 2026-07-04). The beschikkingsaftrek is a ruling from the Belastingdienst anticipating the inkomstenbelasting deduction; it lowers the taxable wage for loonbelasting only, does not touch the SVB premium bases, and is not a tax credit (unlike the toeslagen at `LOONBEL`). Its lines are non-singleton, carry a show-on-payslip switch, and have a "zero at year closing" switch: when the year is closed, such a line becomes a flat amount of 0 per period and the deduction stops until a new ruling is entered. `LOONBEL_RAW` looks up the raw loonbelasting directly from the official Belastingdienst lb-maandtabel (`hr.loonbelasting.tabel`) for the `TAX_INC` value and the payslip period-end date — no annualisation (the table is already period-specific). For wages above the table ceiling (XCG 16,670/month) the above-ceiling extension applies: `ceiling_tax + (TAX_INC − ceiling) × 46.5%` (MR 144 § Algemeen). `LOONBEL` then applies the toeslagen as monetary deductions from the raw tax amount — not as reductions to taxable income — flooring the result at zero and returning it as a negative (deduction) value. Because the maandtabel is exclusief basiskorting, the basiskorting (XCG 2,915/year — the loonbelasting withholding basiskorting per AD-13 and the official 2026 *Loonbelastingverklaring*; the 3,247.35 figure is an inkomstenbelasting amount, not the loonbelasting basiskorting) is a required separate deduction applied here automatically to all employees; the remaining toeslagen are stored as annual amounts on employee fields and divided by 12.

### Step 11 — Extra Tax on Bijzondere Beloningen (Seq 110)

When a bijzondere beloning is present (vakantiegeld, bonus, gratificatie, incidentele overuren), a single marginal rate is selected from the separate bijzondere-beloningen table (exclusief basiskorting, 6 bands) by the employee's **jaarloon** — by default the prior-year jaarloon, with a manager override to the current-year jaarloon when unrepresentative — and applied only to the bijzondere beloning amount. The tarief is fixed once per tax year, stored per (employee, year) as the carry-forward default, and the applied rate is recorded on the payslip line (AD-21). The earning stays in `ALW` (AOV/AWW, BVZ and AVBZ premiums apply; ZV/OV follow Step 12, so overtime on this route stays out of the ZV/OV base — decided 2026-10-08, superseding "SVB premiums apply" for ZV/OV) but is excluded from `TAX_INC`. It gets no own AOV/AWW premium room: it counts toward the monthly maximum of the month in which it is paid (Step 6; decided 2026-10-09, superseding the open OQ-16). The rule returns zero when there is no bijzondere beloning. Whether overtime is incidenteel (this table) or regulier (the maandtabel) is a manual payroll-manager choice.

### Step 12 — ZV and OV (Seq 120, 121)

ZV and OV are employer-only and share a wage ceiling of XCG 7,146.10/month (XCG 85,753.20/year). ZV wage (Landsverordening Ziekteverzekering art. 1 and art. 2 lid 2) is every payment for work "in welke vorm ook", so the ZV base is the contract wage plus the Bijtelling wage lines plus the earnings flagged "Include in SVB wage" plus the monthly pro-rata value of fixed periodic payments, capped at that ceiling, each month on its own (decided 2026-10-08, superseding "the contract base wage (excluding fringe benefits)" and AD-14's "overtime included" as far as it applied to ZV and OV; pro-rata periodic payments decided 2026-10-09):

- **Bijtelling** (wage in kind) is in the ZV base at its LLB value, unless the SVB or a ministerial regulation sets another valuation (art. 2 lid 5).
- **Overtime pay is never in the ZV base**, with or without Lei di Bion: the "Include in SVB wage" flag is fixed off for every overtime earning type (`OVT_WD`, `OVT_SAT`, `OVT_SUN`, `OVT_PH`), including exempt and bijzondere-route overtime.
- **Generic taxable earnings** follow their per-line "Include in SVB wage" flag (default on); **untaxed earnings** default off.
- **Fixed periodic payments** (vakantiegeld, a 13th month) that are a structural part of the employment terms: an earning line flagged "vaste periodieke uitkering" carries an annual amount, and annual ÷ 12 enters the ZV/OV base every month; the actual payout of that line is excluded from the ZV/OV base, so it is never counted twice (decided 2026-10-09; mechanism detail in Story 2.10).

ZV and OV use the same SVB wage (decided 2026-10-09, superseding the open OQ-22). They differ in who is insured: ZV covers only employees who work 5 or 6 days a week and whose wage on the peildatum of 1 November of the previous year was below the SVB wage limit; OV covers every employee, regardless of wage or working days. **The module determines ZV insurance itself** *(decided 2026-10-09, superseding the proposed default in which the payroll user ran the peildatum test; open: OQ-24)*: with fewer than 5 working days a week (from the working schedule) it sets the ZV wage line to `enabled = False` at once, and with a wage above the SVB wage limit on the peildatum (1 November of the previous year) for the following calendar year. The payroll user can override this per employee, with a mandatory reason recorded on the employee. The monthly limit of 7,146.10 is taken from the SVB-Tabel-2026 (329.82 per day for a 5-day week × 65 ÷ 3); this table is authoritative over the unindexed 283.26 per day in the published text of the ZV ordinance, which predates indexation under art. 1b (decided 2026-10-08). ZV is a flat 1.9%; OV is variable by gevarenklasse, read from the contract OV percentage field. ZV and BVZ are separate statutory insurances and must not be combined.

### Step 13 — Net Deductions, Carry-Over and Net (Seq 125–130)

*(Decided 2026-10-08, superseding "Net and Non-Taxed Amounts (Seq 130, 140)": the separate `NONTAXED` rule is removed; reimbursements are untaxed earnings inside `ALW`.)*

`NET_PRE` is net before net deductions (hidden, always executes): the BASIC, ALW and DED categories before the net deductions, DED being negative. It is the base for percentage net deductions.

**Net deductions — `NET_DED`, Seq 126 (AD-28).** Deducted from net pay after loonbelasting and premiums; they never reduce `TAX_INC` or any premium base. Uses: garnishment (loonbeslag), loan or advance repayment, union dues, savings, and insurance paid on the employee's behalf. Per line:

- a fixed amount or a **percentage of net**, the percentage base being net **before** or **after** other net deductions (including higher-priority lines of the same kind); payouts (for example a vacation payout) increase that base;
- a **threshold** (a protected amount excluded from the base first), a **maximum per period**, and a **priority** (ascending; earlier lines are served first);
- a **total cap** as a percentage of net across all lines of this kind, checked per line against the amount already deducted (use the same percentage on every line);
- **deduct from balance**: a total to recover that runs until zero, the final period taking only the remainder; the balance is updated only at close (AD-9);
- a **GL account and creditor** (`res.partner`): at close the journal credits that account as a payable to that creditor.

A variant is a net deduction for a health-insurance premium (or similar) that sits **outside** the total cap. The system does not enforce legal garnishment limits: the protected amount comes from the beslag document and the priority is set manually. Bank-payment routing to the creditor's bank account is deferred to v1.1R.

**Net carry-over — `NET_CARRY`, Seq 128 (AD-29; always executes).** Automatic and singleton; nothing is entered. If net pay after all net deductions would be negative, net is set to 0 and the shortfall is carried to the next payroll as a receivable from the employee, deducted there. Tax and premiums are not reduced (art. 11 lid 4 LLB: the shortfall is deemed withheld, and the employer pays the full tax). Detection runs on the final net pay, never on the tax base. The carried balance is stored per employee and written only at run close (AD-9). A negative tax base (for example from a prior-period correction) is a separate scenario and out of scope.

`NET` is the net salary payable: NET = BASIC + ALW + DED, where `DED` includes the net deductions (`NET_DED`), plus the carry-over (decided 2026-10-08, superseding the NET followed by a separately added non-taxed amount). The category of `NET_CARRY`, and how a positive carry-out fits the sign convention, is left to the implementing story (Story 2.17). There is no net rounding: net is paid to the cent; rounding happens only inside the tax and premium tables, and cash-payment rounding is out of scope. The Bijtelling offset (Seq 127, a negative `DED` line) keeps wage in kind out of cash net (decided 2026-10-09, superseding the open OQ-20).

### Step 14 — Total Employer Cost (Seq 150)

An informational aggregate of total loon plus the employer-contribution category plus the BVZ supplement `BVZ_SUPPL` (decided 2026-10-09, superseding "the BVZ supplement lines", which included `BVZ_SUPPL_EXTRA`; decided 2026-10-08, superseding the aggregate in which the BVZ employer share sat in `ER`: the supplement now sits in `ALW` but remains an employer cost). It does not affect net pay and is used for labour-cost reporting only.

### Corrections — Correct from [date]

*(AD-30; decided 2026-10-08.)* For all premiums and loonbelasting, closed periods can be recalculated from an effective date with the correct data (a wrong wage component, a wrong setting, a late-reported status, a late start date). The difference (correct minus withheld or paid) is booked as identifiable correction lines on the current payslip; closed payslips are never changed (AD-9 intact). *(Decided 2026-10-09, superseding the open OQ-15 and OQ-19.)* Within the current year the **TWK method** (terugwerkende kracht) applies: the difference is included in the current month's return, so the cumulative year amounts reconcile again; a separate corrected return for the old month is normally not needed. Corrections over a closed year run through the verzamelloonstaat; if it differs from the monthly returns, a naheffing (ALL art. 16) or a reduction or restitution (ALL art. 39a lid 2; Lv AOV art. 30) follows. When a change is saved with an effective date in a closed month, the system asks: "Je hebt een wijziging doorgevoerd die ingaat per [datum]. Wil je de tussenliggende periodes nu met terugwerkende kracht corrigeren?" with [Ja, corrigeer vanaf [datum]] and [Nee, pas vanaf de huidige maand toepassen]; Ja starts "Correct from [date]". If the effective date falls in a locked year, the system says that the correction over that year cannot be made in the module but runs through the verzamelloonstaat, and offers only to correct from 1 January of the current year. Payslips and returns of a locked year are never recalculated or overwritten. A backdated pay rise is not a correction: back pay is wage in the month it is paid (art. 10 lid 1 LLB) and is an ordinary earning in the current period.

## Enable / Disable Mechanism

Every salary rule that maps to an `hr.employee.wage.line` checks the line's `enabled` flag before computing. When `enabled = False` the rule immediately returns `0.00` without executing its logic, so downstream rules that reference it receive `0.00` rather than an error or a stale value. This lets a payroll administrator disable individual premiums or taxes per employee without modifying the structure or removing lines.

The `active` and `enabled` flags are independent and intentionally distinct:

| Field | Effect when False |
|---|---|
| `active` | Hides the line from the UI and excludes it from calculation |
| `enabled` | Keeps the line visible for audit; returns `0.00` in calculation |

Disabling a premium for audit transparency therefore uses `active = True, enabled = False`, so that the exemption is visible and demonstrably deliberate.

The BVZ exemption is set **per tax year** and overrides the employee's AOV-insured status and BVZ supplement type; when BVZ is exempt, both the supplement and the total premium return `0.00` (decided 2026-10-08, superseding a BVZ gate that was not tied to a tax year).

The enabled flag applies only to premium and tax computation rules, never to the shared income-base intermediates. The following rules always execute regardless of which premiums are enabled (decided 2026-10-08, superseding the list without `NET_PRE` and `NET_CARRY`; the Bijtelling offset added 2026-10-09):

| Seq | Code | Reason |
|---|---|---|
| 20 | BVZ_PREM_INC | Base for BVZ_SUPPL and BVZ_TOTAL (decided 2026-10-09, superseding the list with `BVZ_SUPPL_EXTRA`) |
| 50 | AOV_PREM_INC | Base for AOV/AWW, the surcharge, and AVBZ |
| 80 | TAX_INC | Base for LOONBEL_RAW |
| 90 | LOONBEL_RAW | Base for LOONBEL |
| 125 | NET_PRE | Net before net deductions — base for percentage net deductions |
| 127 | Bijtelling offset (code set by Story 2.11) | Keeps wage in kind out of cash net — always required |
| 128 | NET_CARRY | Net carry-over in and out — always required |
| 130 | NET | Final output — always required |
| 150 | TOTAL_ER_COST | Informational aggregate — always required |

A consequence worth stating explicitly: disabling AOV/AWW for an employee aged 67 does not disable `AOV_PREM_INC`, so AVBZ continues to use that base and computes correctly.

# Data Models

The module extends standard models and introduces new ones; the sections below list them. *(Decided 2026-10-08, superseding the fixed count of three extended and five new models: the wage line gains fields and new close-time stores are added.)*

## Extensions to Standard Models

### hr.salary.rule

Extended with a `singleton` boolean (default `True`) that controls whether a wage component may be applied more than once to the same employee. Every wage component is defined here as a Tier 1 global rule.

### hr.version

(Odoo 19: the `hr.version` model in core `hr` replaces the former `hr.contract` — the v3.0D "contract" extension target.) Extended with `l10n_cw_ov_percentage` (Float), the OV gevarenklasse rate fixed per employee for the duration of the contract. In the detailed design phase this interim Float is intended to be replaced by a Many2one to a dedicated `l10n_cw.svb.industry` model holding the official SVB gevarenklasse list (deferred — see roadmap).

### hr.employee

Extended with annual toeslag fields used as monetary deductions from computed tax: `l10n_cw_only_earner_deduction` (alleenverdienerstoeslag), `l10n_cw_child_deduction` (kindertoeslag, cumulative), and `l10n_cw_old_age_deduction` (ouderentoeslag).

Also extended with the BVZ and AOV/AWW status facts (decided 2026-10-08, superseding fixed per-employee BVZ percentages; the implementing story places each field on `hr.employee` or `hr.version` and names it):

- **AOV-insured**: stored once per employee and date-effective (it can change mid-year, for example at 65). It drives the BVZ rate and the AOV/AWW liability.
- **AOV/AWW override**: an AOV/AWW-specific override of the AOV-insured status (for example AWW art. 26 lid 2 sub b).
- **BVZ supplement type**: `statutory` (derived: 9.3% when AOV-insured, 2.8% when not), `full`, or `none` (only without a current employment, validated against the contract type, never for a DGA).
- **BVZ exempt**: a per-year switch, held through the BVZ `enabled` gate set per tax year; it overrides the two BVZ fields above.

The beschikking is no longer a single field on the employee: it is held as beschikkingsaftrek wage lines on `hr.employee.wage.line` (decided 2026-10-08, superseding the single employee-level beschikking field). Tracking a ruling that runs over several years is deferred to v1.2R; until then a beschikkingsaftrek line is entered per year and zeroed at year closing (recorded 2026-10-09 from Tech Design v5.0D).

The employee carries only a derived, read-only Lei di Bion indicator ("covered by Lei di Bion <year>"), computed from the annual Lei di Bion approval record; the approval itself is never held on the employee (decided 2026-10-08, superseding any Lei di Bion approval tied to an employee beschikking field).

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

The wage line also carries the following settings (AD-25 to AD-28; decided 2026-10-08, superseding a wage line that held only the enable flag and one parameter). Field names are left to the implementing stories, except where shown:

- **Validity and amount**: `date_from` / `date_to`, an amount, an amount basis (annual ÷ 12 or per period), recurring or one-time (one-time resets to 0 at run close), and a show-on-payslip switch.
- **Calculation settings**: basis (included items or hours), factor (percentage, hourly rate standard or SVB-wage based (OQ-13 resolved 2026-10-09), or multiplier), include base wage, base amount, and the caps per period, per year and lifetime.
- **Earning flags**: Include in SVB wage (ZV/OV only; fixed off for every overtime earning type, decided 2026-10-08), taxed as bijzondere beloning, `is_untaxed` with the legal ground (art. 6F lid 1 sub …), and **vaste periodieke uitkering** with an annual amount, whose monthly pro-rata (annual ÷ 12) feeds the ZV/OV base and the SVB-wage hourly rate while the payout itself stays out of the ZV/OV base (decided 2026-10-09).
- **Beschikkingsaftrek**: the zero-at-year-closing switch.
- **Net deduction**: fixed amount or percentage of net (base before or after other net deductions), threshold, maximum per period, priority, total-cap percentage or outside the total cap, deduct from balance, GL account and creditor (`res.partner`).

### Lei di Bion approval record

*(AD-23; decided 2026-10-08, superseding "`hr.lei.di.bion.beschikking` or a dated approval field with valid_from/valid_to".)* An employer-level record per company and calendar year, with a header and employee lines. Model and field names are left to the implementing story (Story 2.9).

- **Header**: company, calendar year, request date, status (requested / approved / deemed approved / rejected), beschikking number and date, **valid from / valid through dates** (normally the whole calendar year), attached document, and the deemed-approval date, set automatically to the request date + 2 weeks. The request is due within two weeks after the start of the calendar year or after the start of employment (decided 2026-10-09). The approval carries the **dates from which and through which it is valid** — normally the whole calendar year — and the employer must have received it in time to calculate the first payroll of the year; overtime is exempt only on a payslip whose period end (`date_to`) falls inside that validity window (decided 2026-10-08).
- **Lines**: the employees covered, each with the estimated overtime hours from the request and the **prior-year wage** (gross, excluding overtime, including vakantiegeld and bonuses). The prior-year wage is filled from the module's year-to-date data; when the module has no prior-year data (a new employee, the first year of use, migrated data) the approver enters it manually. When a line is added, the module checks that amount against the income limit and blocks the line if it is above (decided 2026-10-09, superseding a line with estimated hours only; OQ-21).

The record is entered and approved by the Payroll Manager. The employee's read-only indicator is derived from it.

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
| `tax_type` | Selection | `bijzondere_beloning` / `basiskorting` / `verwervingskosten` / toeslag types |
| `active` | Boolean | Active flag |

`hr.tax.bracket` holds the bijzondere-beloningen rates and the Belastingdienst scalars (basiskorting, verwervingskosten, toeslagen) only. **SVB premiums and ceilings are not here** — they moved to the per-year `hr.svb.parameters` record (AD-22), so each shared ceiling is stored exactly once. `bijzondere_beloning` is read via `lookup_marginal_rate` (single band rate at the jaarloon; AD-21); the dated scalars via `compute_tax(tax_type, date)` (its surviving role). Loonbelasting uses `hr.loonbelasting.tabel.lookup_loonbelasting` (AD-20). All three stores are dated and append-only.

### Close-time stores

Four stores hold state that changes only at run close (AD-9, AD-29; decided 2026-10-08). Their model and field names are left to the implementing stories.

- **Lifetime accumulator**: the running total per wage line across years, for the cumulative (lifetime) maximum of the calculation settings. `hr.wage.component.ytd` holds annual totals only and cannot serve this.
- **Carry-over balance**: the net shortfall per employee carried to the next payroll as a receivable from the employee.
- **Net-deduction balance**: the remaining amount to recover per net-deduction line that deducts from a balance.
- **Year lock**: per tax year, set by year closing; no further runs and no changes to that year's data afterwards. The lock cannot be cleared inside the module (decided 2026-10-08, superseding a lock that the controlled reopen could lift).

# Tax and Rate Management

## 2026 Loonbelasting Table

Applied to the periodic fiscal wage (`TAX_INC`) using the official Belastingdienst Curaçao lb-maandtabel, published annually per Ministeriële Regeling. The lb-maandtabel is the statutory instrument for loonbelasting withholding (a prepayment of inkomstenbelasting). The Schijventarief (progressive bracket table) is the annual inkomstenbelasting instrument — it is not the correct instrument for employer withholding and must not be used for loonbelasting calculation.

The lookup method: `wage_from = floor(TAX_INC / 5.00) * 5.00`; read the corresponding row from `hr.loonbelasting.tabel.lijn`. Above the table ceiling (XCG 16,670/month): `ceiling_tax + (TAX_INC − 16,670) × 46.5%` (MR 144 § Algemeen). Missing table (neither a current-year nor a still-open prior-year header) raises `UserError` (AD-18). The 2026 maandtabel has ≈ 3,335 rows and is seeded as `data/hr.loonbelasting.tabel.lijn.csv`.

**Versioning and correction handling:** The `hr.loonbelasting.tabel` header model carries fields `name`, `period_type`, `year` (Integer), `valid_from`, `valid_to`, and `active`. Multiple versions of the same (period_type, year) are supported — the Belastingdienst occasionally publishes a corrected table mid-year. The selection rule picks the active record with the latest `valid_from ≤ payslip.date_to`; ties (same `valid_from`) are broken by `id desc` (most recently uploaded). A retroactive correction (same `valid_from` as the original) is automatically preferred for herberekening of all prior payslips in that year. A prospective correction (later `valid_from`) applies only to payslips from that date onward. **Prior-year fallback** (decided 2026-10-04, superseding the current-year-only selection): only headers for the payslip's year or the year before qualify, the current year first. If the new year's table is not yet uploaded at the first run of the year, the prior year's still-open table (`valid_to` empty) is used until the new one arrives; a closed or older table does not qualify. This fallback applies only to the loonbelasting table — SVB parameters never fall back to a prior year (AD-22).

The 2026 maandtabel is published **exclusief basiskorting** (it taxes from the first gulden), so the basiskorting is subtracted separately afterward (it is not already in the table). Example: TAX_INC = XCG 3,245.00 → lookup wage_from = 3,245 → loonbelasting = XCG 316.39 raw. Above-ceiling example: wage 20,000 → 4,862.91 + 46.5% × (20,000 − 16,670) = XCG 6,411.36.

## 2026 Toeslagen

Applied as monetary deductions from the computed tax, not as income reductions. The basiskorting applies automatically to all employees; the rest are stored as annual amounts on employee fields.

| Toeslag | Annual Amount (XCG) | Source |
|---|---|---|
| Basiskorting | 2,915 | Automatic — all employees (loonbelasting basiskorting per AD-13; the 3,247.35 figure is an inkomstenbelasting amount, not this) |
| Alleenverdienerstoeslag | 1,779 | `l10n_cw_only_earner_deduction` |
| Kindertoeslag — 1st child | 948 | `l10n_cw_child_deduction` (cumulative) |
| Kindertoeslag — 2nd child | 475 | Added to above |
| Kindertoeslag — 3rd child | 124 | Added to above |
| Kindertoeslag — 4th child+ | 96 | Added to above |
| Ouderentoeslag (standard) | 1,342 | `l10n_cw_old_age_deduction` |
| Ouderentoeslag (reduced) | 673 | Alternative value |

## 2026 Bijzondere Beloningen Rate Table

The exclusief basiskorting variant is used (basiskorting applied once via the maandtabel, so it is not applied again here). The marginal rate is chosen by the employee's **jaarloon** — by default the prior-year jaarloon, with a manager override to the current-year jaarloon when unrepresentative (AD-21) — and applied only to the bijzondere beloning. **Six bands** (the official 2026 PDF; v3.0D earlier listed five, omitting the 30% band):

| Jaarloon (XCG) | Rate |
|---|---|
| 0 – 43,500 | 9.75% |
| 43,500 – 58,000 | 15.00% |
| 58,000 – 86,900 | 23.00% |
| 86,900 – 123,100 | 30.00% |
| 123,100 – 181,000 | 37.50% |
| > 181,000 | 46.50% |

## 2026 SVB Premium Rates

*(Decided 2026-10-08, superseding the BVZ split into a 4.3% employee and a 9.3% employer share and the annual-ceiling-only figures for AOV/AWW and AVBZ.)* For BVZ the whole premium is the employee's premium; the "Employer %" column shows the employer supplement paid to the employee.

| Premium | Employee % | Employer % | Annual Ceiling (XCG) |
|---|---|---|---|
| AOV/AWW (combined) | 6.5% | 9.5% | 100,000 (monthly maximum 8,333.33) |
| AOV above ceiling (employee only) | 1.0% | — | No ceiling (on the excess above the monthly maximum) |
| AVBZ | 1.5% | 0.5% | 606,247.08 (monthly maximum 50,520.59) |
| BVZ — AOV-insured | 13.6% total premium | 9.3% supplement (statutory) | 150,000 (running total, pro-rated from the start of insurance or employment) |
| BVZ — not AOV-insured (pensioner) | 6.5% total premium | 2.8% supplement (statutory; Landsbesluit BVZ art. 7 lid 2) | 150,000 (as above) |
| ZV | — | 1.9% | 85,753.20 (monthly cap 7,146.10) |
| OV | — | 0.5%–5.0% (by gevarenklasse) | 85,753.20 (shared with ZV; monthly cap 7,146.10) |

The 2.8% pensioner supplement comes from Landsbesluit BVZ art. 7 lid 2; the SVB-Tabel-2026 lists only the 6.5% rate. It is stored in `hr.svb.parameters` next to the 6.5% pensioner rate (decided 2026-10-08). Per the official SVB-Tabel-2026, AVBZ and BVZ employee shares are **flat** (no income-graduated scale); the earlier "AVBZ 0.5%/1.5% at 29,897.44" and "BVZ sliding 0%–4.3% (12,000/18,000)" do not exist and are dropped (AD-5/AD-22). The ZV/OV loongrens is a **monthly** cap (XCG 7,146.10) applied directly — no annualisation. All SVB rates and ceilings live in the per-year `hr.svb.parameters` record (AD-22).

**Ceiling methods (decided 2026-10-08, superseding the 2026-07-08 AD-24 rule that applied a cumulative annual maximum to AOV/AWW, BVZ and AVBZ).** AOV/AWW (8,333.33), AVBZ (50,520.59), ZV and OV use a **monthly maximum**: each month stands alone, and differences are settled through the employee's annual assessment. Only BVZ uses a **running total** (AD-24): premium on the year-to-date premie-loon capped at a ceiling pro-rated from the start of insurance or employment, minus the premium base already used, at this period's rate. None of the methods uses per-month ×12 annualisation. Below any ceiling the result equals flat-rate × base, so ordinary monthly payslips are unchanged.

**Lei di Bion exempt overtime (AD-23).** Exempt overtime is paid free of *both* loonbelasting and SVB premiums (0% / 0%) and is excluded from both `TAX_INC` and the premium bases while still paid in net (art. 6F lid 1 sub v and lid 5–6 LLB). *(Decided 2026-10-08, superseding the approval as an employer beschikking held per employee, `hr.lei.di.bion.beschikking`, or a dated approval field with valid_from/valid_to.)* The approval is an **employer-level, per-calendar-year** record (see Data Models): the employer requests it within two weeks after the start of the calendar year or after the start of employment (decided 2026-10-09), with the overtime register (Arbeidsregeling art. 30) and an estimate of overtime per employee. The Inspecteur decides by beschikking within two weeks; without a timely decision the request **counts as approved**, and the deemed-approval date is set automatically to the request date + 2 weeks. At the request the employee must have worked overtime regularly in the past 12 months (at least 6 months), and the employer must have filed the previous year's verzamelloonstaat (art. 6F lid 1 sub v LLB; Toelichting overwerkregistratie 2026); these are checked by the employer when filing, not computed by the module (decided 2026-10-09). In the module, the Payroll Manager enters and approves the record (the AD-23 senior gate). Overtime is exempt only if **all** of the following hold:

1. the employee is on a line of an approved or deemed-approved record for that year, checked at `payslip.date_to` (AD-17);
2. the overtime is within 10 hours per week, 40 hours per month and 520 hours per year: the approver enters the eligible exempt hours manually, and the engine computes no cap (40/month and 520/year added 2026-10-09);
3. the employee's gross annual income stays at or below the income limit of Arbeidsregeling art. 3: **XCG 85,753.20** gross per year, excluding overtime and including vakantiegeld and bonuses, tested at the request on the **prior-year** wage (the line's prior-year wage, see Data Models). The limit is a statutory amount held as one fixed dated limit amount (AD-5) in `hr.tax.bracket` with `tax_type` `lei_di_bion_inkomensgrens` and only compared (annual wage ≤ limit) — no `compute_tax()`, no brackets *(decided 2026-10-09, superseding "read via `compute_tax()`")*; it is never read from `hr.svb.parameters`, even though it equals the ZV/OV annual wage limit. During the year the module warns when the forecast annual wage exceeds the limit; if it is exceeded, the exemption is corrected manually with "Correct from [date]" (D8 / AD-30). Whether the exemption lapses when the limit is exceeded during the current year, and from when, is open (OQ-26). *(Decided 2026-10-09, superseding a current-year forecast as the only test and the open OQ-21.)* Sources: the Belastingdienst page "Vrijstelling van loonbelasting en sociale lasten mogelijk dankzij Lei di Bion" (https://belastingdienst.cw/vrijstelling-van-loonbelasting-en-sociale-lasten-mogelijk-dankzij-lei-di-bion/) and the request guidance "Verzoek vrijstelling LB en Sociale lasten Overwerkloon (Lei di Bion)" (`docs/Toelichting-overwerkregistratie-2026.pdf`).

Overtime that does not meet all three conditions falls back to a taxable route (regulier → maandtabel, or incidenteel → bijzondere). Exempt or not, overtime never enters the ZV/OV base (Step 12). The employee shows only a derived, read-only indicator ("covered by Lei di Bion <year>").

## Rate Update Procedure

Rates change without code deployment. The administrator opens Salarisadministratie → Configuratie → Tarieven, first records the new values with the updated `valid_from` and rates, and only then sets `valid_to` on the records they replace (decided 2026-10-09, superseding the order "set `valid_to` on all expiring records, then create new records"). For the loonbelasting table, leave the prior year's `valid_to` empty until the new year's table is uploaded — closing it early disables the prior-year fallback (decided 2026-10-04). The SVB parameters have no fallback: without an `hr.svb.parameters` record for the new year the calculation stops (AD-18/AD-22; decided 2026-10-09). Historical records are never deleted, because they are required to recompute prior payslips correctly.

# Payroll Run Lifecycle

The payroll run progresses through three states — CONCEPT (draft) → TE CONTROLEREN (verify) → AFGESLOTEN (close) — while individual payslips progress CONCEPT → TE CONTROLEREN → BEVESTIGD (done), with GEANNULEERD (cancel) available as a side branch before close. Recomputation (herberekening) is permitted in any state before close, so corrections can be made without reverting a posted journal entry. For BVZ only, a herberekening also recomputes later confirmed periods in ascending order (forward cascade, AD-24; decided 2026-10-08). See Figure 3.

## On Close

Closing the run is the single point at which the system commits results. The `action_close()` method performs the following, in order:

1. Confirm all payslips in the run (status → done).
2. Lock the payslips against further editing.
3. Iterate each confirmed payslip's lines and locate or create the corresponding `hr.wage.component.ytd` record.
4. Increment `ytd_amount` by each line amount and update `last_updated` and `last_payslip_id`.
5. Write the close-time state (AD-29; decided 2026-10-08): the net carry-over balance per employee, the net-deduction balances, the lifetime accumulators of the calculation settings, and the reset to 0 of one-time wage lines.
6. Generate and post the accounting journal entry (`account.move`: DRAFT → POSTED).
7. Make the run-level reports available (B-01, B-02, B-05, A-01).

*(Decided 2026-10-08, superseding the six-step close that committed only payslips, YTD and the journal.)* All of these state changes happen in `action_close()` only (AD-9).

After the last run of the calendar year, the year-end reports (B-03, B-04, B-06, B-07) are produced from the accumulated YTD records.

## Year Closing

*(AD-29; decided 2026-10-08.)* When closing a run, the user can mark it as **the last run of the year**; the system asks for confirmation before proceeding. The confirmation tells the user to make an Odoo.sh backup before the year close, because restoring that backup is the only way to change a locked year (see Reopen). This message is derived from the restore procedure (decided 2026-10-08). A year close is a monthly close plus:

- the year is **locked**: no further runs for that year and no changes to that year's data afterwards;
- the year-end actions run: beschikkingsaftrek lines with "zero at year closing" set become 0, any remaining BVZ year-end settlement is made, and one-time lines are reset.

## Reopen

The controlled reopen applies to monthly runs of an **unlocked** year and must reverse every close-time mutation: the carry-over balance, the net-deduction balances, the lifetime accumulators, the one-time resets and the beschikkingsaftrek zeroing.

A **locked year cannot be reopened inside the module** (decided 2026-10-08, superseding "a locked year cannot be reopened except by the explicit controlled reopen"). The only way to change a locked year is to restore the Odoo.sh backup taken before the last payroll run of that year and redo that run. If the payroll manager has already entered a new licence after the year close, the restore is allowed only with permission of the provider of this payroll module; what the licence is, how it is entered and how that permission is given and recorded is not yet specified (OQ-23).

TODO(nroosje, 2026-10-08): double-check that a locked year can only be undone by restoring the backup taken before its last run, and tell Claude the outcome - restore-only accepted for now pending the PO's review.

# Accounting Integration

Closing a run posts a balanced journal entry. The GL account numbers below are indicative; final numbers are configured to match the company's Chart of Accounts (deferred to v1.1R). *(Decided 2026-10-08, superseding the mapping with `BVZ_ER`/`BVZ_EMP` and a separate non-taxed reimbursement debit and credit: untaxed earnings are now inside NET, the BVZ supplement is an employer cost, the total BVZ premium is payable to the SVB, net deductions are payable to their creditors, and the carry-over is a receivable from the employee. Accounts without an indicative number are mapped at onboarding or per wage line.)*

| Rule(s) | Side | GL (indicative) | Description |
|---|---|---|---|
| TOTAL_LOON + EARNING | Debit | 6100 | Salary expense (gross incl. Bijtelling and generic earnings) |
| AOV_AWW_ER | Debit | 6200 | Employer AOV/AWW cost |
| AVBZ_ER | Debit | 6210 | Employer AVBZ cost |
| BVZ_SUPPL | Debit | 6220 | Employer BVZ cost (the whole supplement paid to the employee; decided 2026-10-09, superseding `BVZ_SUPPL` + `BVZ_SUPPL_EXTRA`) |
| ZV_ER | Debit | 6230 | Employer ZV cost |
| OV_ER | Debit | 6240 | Employer OV cost |
| UNTAXED_EARN | Debit | 6260 | Onbelaste vergoedingen (employer cost) |
| NET_CARRY (carry-out) | Debit | Mapped at onboarding | Receivable from the employee for the net shortfall |
| Bijtelling offset (Seq 127) | Credit | Mapped at onboarding | In-kind counter-account: wage in kind not paid in cash (decided 2026-10-09) |
| NET | Credit | 2100 | Net salary payable to employees |
| LOONBEL + EXTRA_TAX | Credit | 2200 | Loonbelasting payable to Belastingdienst CW |
| AOV_AWW_EMP + AOV_AWW_ER + AOV_AWW_1PCT | Credit | 2300 | Total AOV/AWW payable to SVB |
| AVBZ_EMP + AVBZ_ER | Credit | 2310 | Total AVBZ payable |
| BVZ_TOTAL | Credit | 2320 | Total BVZ premium payable to SVB |
| ZV_ER | Credit | 2330 | ZV payable to SVB |
| OV_ER | Credit | 2340 | OV payable to SVB |
| NET_DED | Credit | Per wage line | Payable to the creditor (`res.partner`) of each net-deduction line |
| NET_CARRY (carry-in) | Credit | Mapped at onboarding | Settlement of the receivable from the employee |

The Bijtelling offset credits an in-kind counter-account (indicative, mapped per company at onboarding), so the Bijtelling included in the 6100 debit is matched by a credit even though it is not paid in cash (decided 2026-10-09, superseding the open OQ-20).

## Balance Identity

Total debit equals salary expense (including Bijtelling and generic earnings) plus untaxed earnings plus the BVZ supplement (`BVZ_SUPPL` only; decided 2026-10-09, superseding the supplement split over `BVZ_SUPPL` and `BVZ_SUPPL_EXTRA`) plus all other employer contributions plus any carry-out receivable. Total credit equals net payable plus all tax and premium payables (including the total BVZ premium) plus the creditor payables for net deductions plus the in-kind counter-account credit for the Bijtelling offset plus any carry-in settlement. By the definition of NET (BASIC + ALW = NET + all employee deductions, where `ALW` contains the untaxed earnings and the BVZ supplement and `DED` contains the total BVZ premium, the net deductions and the Bijtelling offset; offset added 2026-10-09), each debit has a matching credit, so debit equals credit by construction (decided 2026-10-08, superseding the identity that added non-taxed reimbursements on both sides).

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
| B-02 | Aangifte SVB Premies | Monthly SVB premium declaration (all premiums, both shares; BVZ as the total premium withheld plus the employer supplement — decided 2026-10-08, superseding separate BVZ employer/employee shares) | `hr.payslip.line` | v1.0R |
| B-03 | Loonbelastingkaart (Jaaropgaaf) | Annual wage tax statement per employee | `hr.wage.component.ytd` | v1.1R |
| B-04 | Verzamelloonstaat CSV | Annual collective wage statement in official CSV format | `hr.wage.component.ytd` | v1.1R |
| B-05 | Salarisjournaalboeking | Balanced payroll journal entry summary per run | `account.move` | v1.0R |
| B-06 | Loonkostenrapport per Medewerker (YTD) | YTD labour cost per employee | `hr.wage.component.ytd` | v1.1R |
| B-07 | Loonkostenrapport per Afdeling (YTD) | YTD labour cost by department | `hr.wage.component.ytd` | v1.1R |
| B-08 | ZV Ziekengeld Overzicht | ZV sick pay overview per run for SVB reimbursement claim | `hr.payslip.line` | v1.1R |
| B-09 | Batch Salarisbetaling Export | Bank payment file (format per bank) | `hr.payslip` | TBD |

# Security and Access Control

The four user groups (see Users and Roles) enforce least privilege. A record rule restricts employees to their own final payslips (state filter decided 2026-10-06, Story 1.3 review):

```xml
<record id="rule_payslip_employee_own" model="ir.rule">
    <field name="name">Employee: own payslips only</field>
    <field name="model_id" ref="hr_payroll.model_hr_payslip"/>
    <field name="groups" eval="[(4, ref('group_l10n_cw_employee'))]"/>
    <field name="domain_force">[('employee_id.user_id', '=', user.id), ('state', 'in', ('validated', 'paid'))]</field>
</record>
```

Because Odoo combines the rules of all groups a user holds, the Accountant group carries its own all-payslips rule, so an Accountant who also holds the Employee role still reads every payslip.

## Data Protection

Payroll data is personal data under the Landsverordening bescherming persoonsgegevens (A.B. 2010 no. 84). The module applies least privilege via group-based access, an audit trail via `mail.thread` on all custom models, append-only tax bracket records, and no transmission of payroll data to external services.

# Configuration and Deployment

## Seed Data Installed with the Module

The `CWMONTHLY` structure type and `CWSTAFF` structure; all salary rule categories and rules (Steps 10–150); the 2026 lb-maandtabel (≈ 3,335 rows, `hr.loonbelasting.tabel` + `.lijn`); the 2026 SVB premium rates and ceilings; and the 2026 bijzondere beloningen rate records (6 correct bands).

## Per-Organization Configuration at Onboarding

The GL account mapping (mapping the indicative numbers to the company Chart of Accounts); the OV gevarenklasse percentage per contract; the toeslag fields per employee; security group assignments; the payslip distribution mechanism; and the Tier 2 component sets and their application to employees (Tier 3). Also, decided 2026-10-08: the employee receivable account for the net carry-over; the GL account and creditor per net-deduction line; and per employee the AOV-insured status and BVZ supplement type.

## Working Hours Normalization

Monthly hours are normalized as `(8h × 5d × 52wk) / 12 = 173.33 hrs/month`, used as the divisor to derive the hourly rate from the monthly contract wage. This assumes a standard 40-hour, five-day week.

## Module Manifest

The module is published as version `19.0.0.1.0`, category `Human Resources/Payroll` (the category used by every shipped `l10n_*_hr_payroll` module; chosen to keep a future official Odoo payroll-localization track open — decided 2026-07-07, superseding the v3.0D `Accounting/Localizations/Payroll`), license `OPL-1`, country `cw`, `installable` and not auto-installed.

# Open Questions and Assumptions

The following items are within scope but require explicit decisions before the affected components can be designed in detail. They do not block the v1.0R milestone unless stated. OQ-13 to OQ-23 were added and OQ-08 was resolved on 2026-10-08; OQ-14, OQ-16 and OQ-17 were resolved on 2026-10-09, and OQ-13, OQ-15 and OQ-18 to OQ-22 later the same day from Tech Design v5.0D and the PO's answers; of the OQ-13 to OQ-23 series only OQ-23 is open. OQ-24 to OQ-26 were added on 2026-10-09 (open, non-blocking).

| # | Item | Decision required | Blocks |
|---|---|---|---|
| OQ-01 | Payslip distribution method | Odoo Employee Portal, Employee App, automatic email on close, or a combination; if email, the language (Dutch / Papiamentu / English) | v1.0R onboarding |
| OQ-02 | Verwervingskosten disable option | Option A (always applied to all) vs Option B (disable-able per employee); design notes "pending confirmation" | v1.0R development |
| OQ-03 | Overtime default rates | Confirm 150/150/200/200 against Curaçao labour regulations before v1.0R sign-off | v1.0R sign-off |
| OQ-04 | Granular user-rights configuration | Menus, actions, and editable fields per group, finalized in detailed design | v1.0R detailed design |
| OQ-05 | Final GL account numbers | Company Chart of Accounts not yet finalized; §Accounting numbers are placeholders | v1.1R |
| OQ-06 | Verzamelloonstaat specification | Confirm the portal accepts the 2025+ spec; confirm Lei di Bion field values | v1.1R |
| OQ-07 | SVB gevarenklasse list | Sourcing the complete official list to replace the interim Float with `l10n_cw.svb.industry` | v1.1R |
| OQ-08 | Loan / garnishment scope | Whether balance tracking is in scope; the current statutory bestaansminimum and how it is stored. **Resolved 2026-10-08 by the PO decision on net deductions:** loans and garnishments are v1.0R net deductions with balance tracking; the system does not enforce legal garnishment limits (the protected amount comes from the beslag document) | Resolved |
| OQ-09 | ZV sick pay design | Waiting-period tracking per episode, cross-period handling, SVB reimbursement tracking, above-ceiling pay policy | v1.1R |
| OQ-10 | Batch payment format (B-09) | Curaçao bank payment file formats to be researched and confirmed | TBD |
| OQ-11 | Vacation first-year proration basis | Answered for the grant side by monthly accrual, partial months pro rata (decided 2026-10-08, superseding the 1 January grant). Remaining: the partial-month basis (calendar days vs working days); see `docs/design/cw-vacation-accrual-v1.1R.md` | v1.1R |
| OQ-12 | Vacation carryover take-window | Confirm which Curaçao employers qualify as continuous operation (6-month vs 3-month window to take carried-over days); see `docs/design/cw-vacation-accrual-v1.1R.md` | v1.1R |
| OQ-13 | Hourly wage "SVB wage" variant | **Resolved 2026-10-09:** the SVB-wage hourly rate = (base wage + fixed allowances + commissions + the monthly reserve for fixed periodic payments such as vakantiegeld or a 13th month) ÷ 173.33; the reserve is annual ÷ 12 of each earning line flagged "vaste periodieke uitkering"; incidental overtime never counts (decided 2026-10-09, superseding the open meaning of the variant) | Resolved |
| OQ-14 | Tax treatment of the BVZ supplement | **Resolved 2026-10-09:** the BVZ supplement is not wage (art. 6F lid 1 sub l LLB): untaxed and outside every premium base (AOV/AWW, BVZ, AVBZ, ZV/OV), also under supplement type `full`. `BVZ_SUPPL` holds the whole supplement and the separate `BVZ_SUPPL_EXTRA` line (Seq 31) is removed (decided 2026-10-09, superseding the statutory contradiction and the interim separate line for the part above the statutory supplement) | Resolved |
| OQ-15 | Correction reporting procedure | **Resolved 2026-10-09:** within the current year the TWK method: the difference goes into the current month's return so the cumulative year amounts reconcile, and a corrected return for the old month is normally not needed; a closed year is corrected through the verzamelloonstaat, followed by a naheffing (ALL art. 16) or a reduction or restitution (ALL art. 39a lid 2; Lv AOV art. 30). Legal framework: monthly return per calendar month (ALL art. 8 lid 3) (decided 2026-10-09, superseding the open reporting method) | Resolved |
| OQ-16 | Premium room for a bijzondere bonus | **Resolved 2026-10-09:** a bonus taxed via the bijzondere table gets no own AOV/AWW premium room; the maximum applies per pay period (Gezamenlijke beschikking AOV/AWW en loonbelasting 1976, art. 6 lid 2) and the bonus belongs to the wage of the month it is paid in (LLB art. 8 lid 6) (decided 2026-10-09, superseding the open Belastingdienst check) | Resolved |
| OQ-17 | Who pays the AOV 1% above the ceiling | **Resolved 2026-10-09:** the 1% above the AOV/AWW monthly maximum is the employee's own premium (Lv AOV art. 26 lid 3); the employer's toeslag (Lv AOV art. 58) does not cover it and the employer pays no surcharge (decided 2026-10-09, superseding the open Belastingdienst check) | Resolved |
| OQ-18 | SVB acceptance of BVZ above 1/12 per month | **Resolved 2026-10-09:** the Belastingdienst and the SVB accept a monthly return on the periodic or the cumulated limit; the BVZ running total stays, and the fallback of a company-level BVZ monthly maximum is dropped. Legal reference: BVZ is levied over the zuiver voljaarsloon (Lv BVZ art. 22 lid 3) (decided 2026-10-09, superseding the open acceptance question) | Resolved |
| OQ-19 | BVZ annual recalculation vs generic correction | **Resolved 2026-10-09:** the per-employee Retroactive switch is removed; past-dated changes are corrected only with "Correct from [date]", which the system offers when a change with a past effective date is saved; a locked year is never recalculated and is corrected through the verzamelloonstaat. The age-65 AOV-insured suggestion moved to Steps 3–4 (decided 2026-10-09, superseding the BVZ-specific option built as requested) | Resolved |
| OQ-20 | Bijtelling in-kind presentation in net | **Resolved 2026-10-09:** Bijtelling stays inside `TOTAL_LOON` (`BASIC`) as its own payslip line; the Bijtelling offset (Seq 127, negative `DED`, never gated, code set by Story 2.11) deducts it again from net and credits an in-kind counter-account mapped at onboarding (decided 2026-10-09, superseding the open "offset line or separate category") | Resolved |
| OQ-21 | Lei di Bion income limit | **Resolved 2026-10-09:** XCG 85,753.20 gross per year, excluding overtime and including vakantiegeld and bonuses, tested at the request on the prior-year wage (from YTD, or entered by the approver when the module has no prior-year data), blocking the line above it; an in-year warning on the forecast; held in `hr.tax.bracket` `tax_type` `lei_di_bion_inkomensgrens`. Also: at most 40 exempt hours per month and 520 per year, regular overtime in at least 6 of the past 12 months, the prior-year verzamelloonstaat filed. Sources: the Belastingdienst page "Vrijstelling van loonbelasting en sociale lasten mogelijk dankzij Lei di Bion" (https://belastingdienst.cw/vrijstelling-van-loonbelasting-en-sociale-lasten-mogelijk-dankzij-lei-di-bion/) and the request guidance "Verzoek vrijstelling LB en Sociale lasten Overwerkloon (Lei di Bion)" (`docs/Toelichting-overwerkregistratie-2026.pdf`) (decided 2026-10-09, superseding the open amount and source) | Resolved |
| OQ-22 | OV wage definition | **Resolved 2026-10-09:** ZV and OV use the same SVB wage (contract wage + Bijtelling + earnings flagged Include in SVB wage + the pro-rata value of fixed periodic payments; never overtime). ZV insures only employees working 5 or 6 days a week whose wage on 1 November of the previous year was below the SVB wage limit; OV insures every employee (decided 2026-10-09, superseding the open OV definition) | Resolved |
| OQ-23 | Licence and provider permission for a restore | What the licence of this payroll module is, how it is entered, and how the provider's permission for restoring a pre-year-close backup after a new licence was entered is given and recorded | Story 3.7 (restore guidance only) |
| OQ-24 | Wage tested on the ZV peildatum | Which wage is tested on the ZV peildatum (the wage level converted to a full year, or the wage earned so far), and the rule for employees hired after 1 November (added 2026-10-09) | Non-blocking (Story 2.10) |
| OQ-25 | AOV/AWW stop at 65 | Does the AOV/AWW premium stop at 65 on the birthday itself (pro rata) or from the next month; the BVZ rate follows (added 2026-10-09) | Non-blocking (Story 2.3) |
| OQ-26 | Lei di Bion exceeded during the year | Does the Lei di Bion exemption lapse when the limit is exceeded during the year, and from when; to be confirmed by the Belastingdienst (added 2026-10-09) | Non-blocking (Story 2.9) |

# Acceptance Criteria

The following must hold before v1.0R is released to production.

**Calculation correctness.** For representative test employees (at minimum: a standard employee, a BVZ-exempt employee, an employee above the AOV/AWW monthly maximum, a not-AOV-insured employee with the 2.8% BVZ supplement, and an employee with a bijzondere beloning; decided 2026-10-08, superseding the set without the pensioner case), loonbelasting and SVB premium amounts match the official 2026 publications within XCG 0.02 (rounding only).

**Balanced journal entry.** Every run close produces an `account.move` where total debit equals total credit, verified across at least ten test payslips of varying salary levels.

**Enable/disable integrity.** Disabling a premium on an employee's wage line yields `0.00` for that premium's lines (for BVZ: both the supplement and the total premium), leaves the other premium and tax lines unchanged, and NET computes without error (decided 2026-10-08, superseding "leaves NET unchanged": with the BVZ supplement inside NET and percentage net deductions reading `NET_PRE`, NET may legitimately change).

**Rate update without deployment.** Setting `valid_to` on a bracket and inserting a new record produces correct tax for payslips dated after the new `valid_from`, with no code change or module upgrade.

**Access control.** A user in `group_l10n_cw_employee` can read only their own payslips and no other employee's payroll data.

**Declarations.** Reports B-01 and B-02 produce correct totals per run, matching the sum of individual payslip line amounts.

**YTD accumulation.** After a run close, each employee's `hr.wage.component.ytd` record reflects the correct running total for the calendar year.

**Structure integrity.** Running payroll on an employee with no special inputs produces a payslip with positive NET for any contract wage above the minimum threshold, with no Python errors or missing rule results.

The following criteria were added on 2026-10-08 for the wage-line, earning, deduction and premium decisions.

**Monthly maximum for AOV/AWW and AVBZ.** In a month whose premium base exceeds XCG 8,333.33, AOV/AWW is computed on 8,333.33 and the 1% surcharge on the excess above it; AVBZ is capped at XCG 50,520.59 per month; no month depends on another.

**BVZ running total.** For an employee insured from mid-year, the BVZ base never exceeds the ceiling pro-rated from the insurance start; a mid-year AOV-insured change applies the new rate and supplement from that period only and produces no negative premium in the change month; the payslip shows the supplement as a "+" line and the total premium as a "−" line.

**Untaxed earnings.** An untaxed earning is paid in net and is excluded from `TAX_INC` and from the AOV/AWW, BVZ and AVBZ bases; it joins the ZV/OV base only with "Include in SVB wage" switched on.

**Net deductions and carry-over.** Net deductions never change `TAX_INC` or any premium base; priority, threshold, caps and balance are respected; when net would be negative, NET is 0, tax and premiums are unchanged, and the shortfall is deducted in the next payroll.

**Close-time state and year closing.** Balances, lifetime accumulators and one-time resets change only at run close, and a controlled reopen of a run in an unlocked year reverses them; after a year close no run can be created and no data can be changed for the locked year, and nothing in the module unlocks it; the year-close confirmation tells the user to make an Odoo.sh backup first (decided 2026-10-08, superseding a controlled reopen that could also lift the year lock).

**Lei di Bion.** Overtime is exempt only for an employee on a line of an approved or deemed-approved annual record at `payslip.date_to`, for the manually entered eligible hours; a record without a timely decision shows a deemed-approval date of request date + 2 weeks; the employee shows only the read-only indicator (decided 2026-10-08). An employee line whose prior-year wage (from YTD or entered manually) exceeds XCG 85,753.20 cannot be added (decided 2026-10-09).

**ZV/OV base.** The ZV and OV base includes the contract wage, Bijtelling, earnings flagged "Include in SVB wage" and the monthly pro-rata of lines flagged "vaste periodieke uitkering" (whose payout month adds nothing extra), never includes overtime of any type, and is capped at XCG 7,146.10 per month (decided 2026-10-08; pro-rata added 2026-10-09).

**Bijtelling offset.** A Bijtelling line raises `TAX_INC` and the premium bases but leaves the cash NET unchanged, and the run's journal entry still balances, with the offset credited to the in-kind counter-account (decided 2026-10-09).

**Correct from [date].** A correction posts identifiable correction lines on the current payslip and leaves every closed payslip unchanged; saving a change with an effective date in a closed month offers the correction, and a date in a locked year offers only a correction from 1 January of the current year (prompt added 2026-10-09).

# Release Roadmap

*(Decided 2026-10-08, superseding the v1.1R placement of loan deductions and garnishments.)*

| Version | Contents |
|---|---|
| v1.0R | Monthly payroll engine, full statutory sequence (Steps 10–150), three-tier wage component model, employee-level dated wage lines, generic taxable and untaxed earnings with calculation settings, beschikkingsaftrek lines, net deductions (including loans and garnishments) and net carry-over, "Correct from [date]", year closing, AOV/AWW and AVBZ monthly maximum, BVZ redesign (supplement and total premium, running total; the retroactive option removed 2026-10-09), loonbelasting + SVB premiums, YTD model, accounting integration, reports A-01/B-01/B-02/B-05, four user groups, Dutch UI translations |
| v1.1R | Final GL account mapping, verzamelloonstaat CSV (B-04), loonbelastingkaart (B-03), labour cost reports (B-06/B-07), ZV sick pay (B-08), statutory vacation accrual (Vakantieregeling 1949) on `hr_holidays`, bank payments / bank interface for net-deduction creditors, Loonbelastingkaart categories for untaxed earnings, additional pay periods, SVB gevarenklasse dropdown |
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
