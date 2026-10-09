::: {custom-style="Title"}
CW Statutory Vacation Accrual (Vakantieregeling 1949) — v1.1R Design Note
:::
::: {custom-style="Subtitle"}
Curaçao Paid-Vacation Tracking — Design Specification
:::

**Status:** deferred design (v1.1R)
**Owner:** l10n_cw_hr_payroll architecture
**References:** PRD `docs/prd/PRD - v3.0D.md` (Out of Scope, Release Roadmap, OQ-11/OQ-12); architecture spine `ARCHITECTURE-SPINE.md` (Deferred table).
**Dependencies:** native `hr_holidays` (already a module dependency).

This note captures the full statutory design for Curaçao paid-vacation tracking. It does **not** change v1.0R scope or code; the feature is a v1.1R build item.

## Statutory rules

- **Annual entitlement = `min(workdays_per_week, 5) × 3`.** The entitlement is keyed to **days worked per week**, not hours. A 6-day week is capped at **15 days** (the law says *at least* fifteen); it is **not** 18. Examples: 5- or 6-day week → 15 days; 4-day → 12; 3-day → 9; 2-day → 6.
- **Part-time nuance:** a 20-hour/week employee spread over 5 days still receives **15 days**, because only days/week reduce the count; hours/FTE do not.
- **Accrued per period (monthly), not granted upfront** (decided 2026-10-08, superseding the 1 January grant). Each month the employee earns 1/12 of the annual entitlement, credited at the **end** of the period, so days are never available before they are earned. Leave is earned by working, new hires and leavers come out right automatically, and the vacation provision stays current. A full-year grant on 1 January is used only where an employment contract explicitly promises it; switching such an employee to accrual needs a transition entry (opening balance at the switch date, accrual from there).
- **Mid-year start proration.** Partial months accrue pro rata, so a mid-year starter needs no separate first-year grant (decided 2026-10-08; this answers the grant side of **OQ-11**). At termination a part-day still rounds up to a whole day (art. 10 lid 2).
- **Seniority extra days are policy, not law.** The Vakantieregeling 1949 has no seniority or age rule. Extra days after N years of service come from the employment contract, a CAO or company policy, and are configured as accrual-plan levels on top of the statutory base level (decided 2026-10-08).
- **Days taken are recorded only in Time Off.** Approved `hr.leave` requests reduce the balance and become paid-leave work entries on the payslip; payroll reads them and never records vacation days itself, so the balance, the provision and the payslip cannot disagree (decided 2026-10-08). Corrections after a confirmed payslip are made on the leave record and settled in the next payslip.
- **Carryover cap.** The accumulated balance is capped at `6 × workdays_per_week`; any excess **lapses**. The outer tax ceiling is art. 6F lid 1 sub f LLB (weekly working hours × 50 weeks at 31 December); a balance above it counts as wage at year end or on termination (art. 6F lid 3). Joined (carried-over) days must be taken within **3 months** of the request, or **6 months** for employers classified as continuous operation (**OQ-12**).
- **Lapse on long absence.** Prior-year vacation rights superannuate if the employee was absent for at least **6 months** due to sickness, or at least **6 weeks** due to legal obligations, in that year.
- **Termination payout.** Unused statutory days are paid out on termination at the statutory day-wage, computed from the remaining Time Off balance; afterwards the balance is set to zero with an allocation correction so it cannot be paid out twice:
  - 5-day week: `monthly_wage × 3 / 65`
  - 6-day week: `monthly_wage × 3 / 78`
  - A part-day is rounded up to a whole day.
- **Public holidays are not vacation.** Public holidays are separate paid free days and are never deducted from the vacation balance.

## Native `hr_holidays` design

The feature reuses Odoo's native leave management as the boring-technology core. The CW localization layer only supplies the entitlement number, proration, carryover/lapse logic, holiday seed, and payout rule.

| CW need | Odoo native vehicle | CW localization layer adds |
| --- | --- | --- |
| Vacation leave type | `hr.leave.type` (allocation-required, day unit, manager validation) | Seed record `Wettelijke Vakantie (CW)` (`CWVAC`) |
| Per-employee accrual | `hr.leave.accrual.plan` (monthly level, credited at period end, pro rata for partial months) + accrual `hr.leave.allocation` | Statutory base level from `min(workdays/week, 5) × 3` per year, per employee from `resource.calendar`; optional seniority levels starting after N years of service (company/CAO policy) |
| Balance + deduct on take | `hr.leave` requests | Free from Odoo (UI, approval, balance) |
| Carryover cap & lapse | Accrual-plan carryover settings + cron | Enforce `6 × workdays_per_week` cap; lapse-on-long-absence adjustment |
| Public-holiday separation | `resource.calendar.leaves` (global time off) | Seed CW public-holiday calendar so leave spanning a holiday consumes no balance |
| Termination payout | Payroll salary rule | New `VAC_PAYOUT` line on final settlement using `×3/65` or `×3/78` day-wage |

- **Source of truth for days/week:** the employee's `resource.calendar` (working schedule), **not** the 173.33-hour monthly normalization (`A-09`), which is hours-based and irrelevant to accrual.
- **Data/seed principle:** entitlement formula and public-holiday calendar are seed/dated data; no hard-coded literals in rule Python.

## Components to build (v1.1R)

### Localization layer

- Seed `hr.leave.type` record `CWVAC` (allocation type, day unit, statutory name).
- Seed CW public holidays as `resource.calendar.leaves` (global time off) — supports both holiday-overtime classification and vacation accrual.
- Accrual plan for `CWVAC` with a monthly statutory base level (credited at period end, pro rata for partial months) and configurable seniority levels; `l10n_cw.leave.accrual` service/model + scheduled action only for what the native accrual plan does not cover:
  - Carryover cap at `6 × workdays_per_week`.
  - Lapse on long absence (sickness ≥ 6 months, legal obligations ≥ 6 weeks).

### Payroll layer

- `VAC_PAYOUT` salary rule for final-settlement payout of unused statutory days. Intersects the calculation engine and reuses the deferred final-settlement flow.

### Reports / UX layer

- Optional: surface the vacation balance on payslip A-01.
- A-02 (leave report) already shows leave days; no structural change required.

## Open questions to resolve before build

| # | Question | Context |
| --- | --- | --- |
| OQ-11 | First-year proration basis | Answered for the grant side by monthly accrual with partial months pro rata (decided 2026-10-08). Remaining: confirm the partial-month basis (calendar days vs working days). |
| OQ-12 | Carryover take-window | Confirm which Curaçao employers qualify as continuous operation (6-month vs 3-month window to take carried-over days). |
| DQ-01 | Days/week extraction | Confirm `resource.calendar` reliably encodes contracted days/week for all target contracts, or whether an explicit `workdays_per_week` field is needed. |
| DQ-02 | Termination flow ownership | v1.0R has no final-settlement flow; `VAC_PAYOUT` depends on that flow being designed in v1.1R. |

## Out of scope / non-goals

- Hard-coded sector-CLA or contractual vacation enhancements above the statutory minimum. They are contractual, not statutory, and are configured as accrual-plan seniority levels per company (decided 2026-10-08).
- Changes to the v1.0R calculation engine or any existing architecture decision.
- Implementation in this design step — this note captures the specification and artifact references only.

*Last updated: 2026-10-08.*
