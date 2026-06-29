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
- **Granted yearly on 1 January.** Each employee receives the statutory grant on the first day of the calendar year; days are deducted as `hr.leave` requests are approved.
- **Mid-year start proration.** An employee who starts mid-year receives a pro-rata grant for the first calendar year. The exact basis (calendar days vs. full grant after a qualifying period) is **OQ-11**.
- **Carryover cap.** The accumulated balance is capped at `6 × workdays_per_week`; any excess **lapses**. Joined (carried-over) days must be taken within **3 months** of the request, or **6 months** for employers classified as continuous operation (**OQ-12**).
- **Lapse on long absence.** Prior-year vacation rights superannuate if the employee was absent for at least **6 months** due to sickness, or at least **6 weeks** due to legal obligations, in that year.
- **Termination payout.** Unused statutory days are paid out on termination at the statutory day-wage:
  - 5-day week: `monthly_wage × 3 / 65`
  - 6-day week: `monthly_wage × 3 / 78`
  - A part-day is rounded up to a whole day.
- **Public holidays are not vacation.** Public holidays are separate paid free days and are never deducted from the vacation balance.

## Native `hr_holidays` design

The feature reuses Odoo's native leave management as the boring-technology core. The CW localization layer only supplies the entitlement number, proration, carryover/lapse logic, holiday seed, and payout rule.

| CW need | Odoo native vehicle | CW localization layer adds |
| --- | --- | --- |
| Vacation leave type | `hr.leave.type` (allocation-required, day unit, manager validation) | Seed record `Wettelijke Vakantie (CW)` (`CWVAC`) |
| Per-employee yearly grant | `hr.leave.allocation` | Scheduled action computes `min(workdays/week, 5) × 3` per employee from `resource.calendar`, creates/updates the 1-Jan allocation, prorated for mid-year start |
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
- `l10n_cw.leave.accrual` service/model + scheduled action for:
  - Annual grant on 1 January.
  - Mid-year start proration (basis pending OQ-11).
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
| OQ-11 | First-year proration basis | Pro-rata by calendar days (`entitlement × days_employed/365`) vs full grant after a qualifying period — the 1949 text does not define it. |
| OQ-12 | Carryover take-window | Confirm which Curaçao employers qualify as continuous operation (6-month vs 3-month window to take carried-over days). |
| DQ-01 | Days/week extraction | Confirm `resource.calendar` reliably encodes contracted days/week for all target contracts, or whether an explicit `workdays_per_week` field is needed. |
| DQ-02 | Termination flow ownership | v1.0R has no final-settlement flow; `VAC_PAYOUT` depends on that flow being designed in v1.1R. |

## Out of scope / non-goals

- Sector-CLA or contractual vacation enhancements above the statutory minimum (those are contractual, not statutory).
- Changes to the v1.0R calculation engine or any existing architecture decision.
- Implementation in this design step — this note captures the specification and artifact references only.

*Last updated: 2026-06-28.*
