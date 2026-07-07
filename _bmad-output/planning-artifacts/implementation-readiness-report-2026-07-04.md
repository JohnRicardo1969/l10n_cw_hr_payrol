---
stepsCompleted: ['step-01-document-discovery', 'step-02-prd-analysis', 'step-03-epic-coverage-validation', 'step-04-ux-alignment', 'step-05-epic-quality-review', 'step-06-final-assessment']
inputDocuments:
  - 'docs/prd/PRD - v3.0D.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-l10n_cw_hr_payrol-2026-06-25/ARCHITECTURE-SPINE.md'
  - '_bmad-output/planning-artifacts/Odoo Module Design Epics - EN - v1.0D.md'
  - '_bmad-output/planning-artifacts/Odoo Module Design Epics - NL - v1.0D.md'
---

# Implementation Readiness Assessment Report

**Date:** 2026-07-04
**Project:** l10n_cw_hr_payroll

## 1. Document Inventory

| Type | File | Status |
|------|------|--------|
| PRD | `docs/prd/PRD - v3.0D.md` (49 KB, whole) | ✓ Found (in `docs/`, cited by epics `inputDocuments`) |
| Architecture | `…/architecture/architecture-l10n_cw_hr_payrol-2026-06-25/ARCHITECTURE-SPINE.md` (55 KB, whole) | ✓ Found |
| Epics & Stories (EN) | `Odoo Module Design Epics - EN - v1.0D.md` (71 KB) | ✓ Found — canonical for assessment |
| Epics & Stories (NL) | `Odoo Module Design Epics - NL - v1.0D.md` (77 KB) | ✓ Found — synced translation |
| UX Design | — | Not present by design (standard Odoo screens; UX-DR001–004 embedded in epics) |

**Supporting references** (cited by epics, not primary planning docs): `docs/tech_design_l10n_cw_hr_payroll_v3.0D.txt`, `docs/design/cw-vacation-accrual-v1.1R.md`.

**Issues:** None blocking. No whole+sharded duplicates. The EN/NL pair is a bilingual set (EN assessed, NL its translation), not a conflict. No missing required documents — the absent standalone UX doc is intentional.

## 2. PRD Analysis (source-of-truth extraction)

The PRD (v3.0D, dated 2026-06-15, **Draft**) does not use numbered FR/NFR IDs. Requirements were extracted from: the five Primary Goals, the User Stories (per role), the Canonical Sequence Map (Seq 10–150, 14 statutory steps), the Enable/Disable mechanism + never-gate table, the Data Models, the Run Lifecycle + `action_close()` steps, the Accounting balance identity, the Reports A-/B-series, Security, and the Acceptance Criteria.

The epics' own Requirements Inventory (FR001–FR036, NFR001–008, AR001–024, UX-DR001–004) was synthesised primarily from the **Architecture Spine** (dated 2026-06-25/29, later than the PRD). This assessment therefore re-derives requirements from the PRD directly and checks them against the epics/stories, rather than trusting that synthesis.

**Key contextual fact:** the Architecture Spine deliberately supersedes the v3.0D tech design / PRD on several statutory points (AD-5, AD-13, AD-14, AD-20, AD-22, AD-23, AD-24). The PRD was *partially* updated to match (it references `hr.svb.parameters`/AD-22, cumulative premiums/AD-24, Lei di Bion/AD-23, the 6-band bijzondere table, the above-ceiling 46.5%) but retains residual pre-architecture content in a few places — the source of the findings below.

## 3. Epic / Story Coverage Validation

Traceability from PRD elements to stories. **Covered** unless noted.

| PRD element | Story coverage | Status |
|---|---|---|
| Statutory sequence Seq 10–150 (all 14 steps) | Epic 2 (2.1–2.11) — matches the PRD Sequence Map exactly | ✓ |
| Overtime 4 types (150/150/200/200) | 2.2 | ✓ (rates = OQ-03, flagged pending) |
| Cumulative annual-ceiling premiums (AD-24) | 2.3/2.4/2.5 | ✓ |
| Loonbelasting table + above-ceiling 46.5% | 2.6 | ✓ |
| Toeslagen as monetary tax deductions | 2.7 | ✓ |
| Bijzondere beloningen (6 bands, AD-21) | 2.8 | ✓ |
| Lei di Bion exempt overtime (AD-23) | 2.9 | ✓ |
| Enable/disable + never-gate set | 2.12 — matches PRD never-gate table exactly | ✓ |
| Three-tier wage model | 1.7, 1.8 | ✓ |
| Dated statutory stores (tax.bracket, svb.parameters, lb-tabel) | 1.4, 1.5, 1.6 | ✓ |
| YTD model + write-on-close | 1.10 + 3.3 | ✓ |
| Run lifecycle + `action_close()` 6 steps | 3.1, 3.3 | ✓ |
| Balanced journal by construction | 3.4 | ✓ |
| Reports A-01, B-01, B-02, B-05 | 4.1–4.4 | ✓ |
| 4 security roles + own-payslip record rule | 1.3 | ✓ |
| Employee toeslag fields + contract OV% + beschikking | 1.9 | ✓ |
| **Employee pension contribution (`PENSION_EMP` input)** | **— none —** | ✗ **GAP (blocking)** |
| `singleton` boolean on `hr.salary.rule` | not explicit in any story | ⚠ minor |

### Finding F1 — Employee pension contribution is unmapped (BLOCKING)

The PRD makes employee pension contribution a **first-class Payroll-User input** in four places: the Payroll-User story ("enter … pension contribution"), the Python context (`inputs.PENSION_EMP.amount`), and its subtraction inside the **BVZ base (Step 2)** and **AOV base (Step 5)**. The v3.0D tech design defines `PENSION_EMP` as a conditional payslip input ("only for employees with a pension arrangement"), not a standalone rule.

Architecture **AD-14** redefined the premium bases positively as `categories.BASIC + categories.ALW`. This **explicitly** removed the verwervingskosten term (moved to `TAX_INC` only) but **silently** removed the `pension_emp` term — no AD rules on employee pension contribution either way. Consequently **no story** provides a PENSION input mechanism or deduction. Of every Payroll-User input, pension is the **only one with no story mapping** (fringe→2.1, beschikking→1.9, overtime→2.2, bijzondere→2.8).

**Impact:** if in scope, pension is cross-cutting — it threads through Story 1.9 (field), a new PENSION input mechanism (absent everywhere), 2.3 (BVZ base), 2.4 (AOV base), 2.6 (`TAX_INC`, via the AOV base), and possibly 2.11 (a `DED` line if the employee bears it). Resolving it after sprint planning means editing several already-written stories.

**Required decision (before sprint planning):** Is employee pension contribution in scope for v1.0R?
- **If yes** → add a PENSION input + the base-deduction stories above, and reconcile AD-14.
- **If no** → record it as an explicit descope in the PRD *Out of Scope* table and roadmap (as was done for Cessantia), so it is a conscious call, not a silent omission.

**Status: CLOSED — decided 2026-07-04.** Premie-loon side resolved (pension **not** deductible — see Legal resolution below; AD-14 vindicated). Loonbelasting side: **IN SCOPE for v1.0R** — the employee pension premium is implemented as a `TAX_INC` aftrekpost via a per-period `PENSION_EMP` payslip input. Story 2.6 (EN + NL) updated: the pension term added to the `TAX_INC` formula, plus an AC specifying the `PENSION_EMP` input and its loonbelasting-only scope. **F1 gate cleared — `/bmad-sprint-planning` is unblocked.**

**Research note (2026-07-04, web sources):**
- **Loonbelasting side — well-supported.** Employee pension premium to a fiscally qualifying fund is deductible from gross income (both employee and employer contributions are tax-deductible). This confirms the PRD's `pension_emp` term as a real pre-tax `TAX_INC` reduction; omitting it over-withholds loonbelasting for pension-holders. (belastingdienst.cw; vidanova-pensionfund.com)
- **Prevalence — material.** Curaçao has a general pension fund (APC) plus company funds; pension arrangements cover a substantial share of the workforce, so this is not a rare edge case. (apc.cw)
- **SVB premie-loon side — uncertain, needs SVB confirmation.** Whether the employee pension premium also reduces the BVZ/AOV *premie-loon* (as PRD Steps 2 & 5 assert) is not clearly established; one source indicates SVB basis handling changed in 2024. **Confirm with the SVB before implementing the premium-base deduction.**
- **Implication for the decision.** Because the loonbelasting deduction is statutorily real and pension is common, a clean "descope entirely" carries correctness risk for pension-holders. A middle path exists: implement the **loonbelasting-side** deduction (`PENSION_EMP` input → reduces `TAX_INC`) in v1.0R, and treat the **premie-loon-side** separately (now resolved — see below).

**Legal resolution — premie-loon side (2026-07-04, primary-source legal analysis by the product owner):** The Landsverordening basisverzekering ziektekosten (P.B. 2013, no. 3) sets the BVZ premium on an income-dependent basis (Art. 6.2, lid 1) and defines *inkomen* (Art. 1.1, onderdeel o) by **direct reference to Art. 3, vierde lid, of the Landsverordening op de inkomstenbelasting 1943** — the *zuivere opbrengst van arbeid*, i.e. income **before** persoonlijke aftrekposten. The employee pension premium is an aftrekpost/persoonlijke last applied **after** the opbrengst van arbeid is determined (to reach belastbaar inkomen). Therefore the pension premium is **not deductible from the BVZ premiegrondslag**.

- **This vindicates AD-14** (premium base = `categories.BASIC + categories.ALW`, no pension term) and confirms the PRD's original Step 2 pension subtraction was **incorrect** for BVZ. **No premium-base story (2.3/2.4) needs pension.**
- The **AOV/AWW** premie-loon should get the analogous check under its own landsverordening, but the epics' `BASIC + ALW` base already excludes pension, so **no story change arises either way**.

**F1 now narrows to the loonbelasting side only.** The sole remaining question: implement the pension premium as a `TAX_INC` (loonbelasting) deduction — an aftrekpost reducing belastbaar loon — in v1.0R, yes/no/defer? If in scope, it touches only a `PENSION_EMP` input (Story 1.9 / a new payslip input) and `TAX_INC` (Story 2.6); the premium bases stay unchanged. This is a materially smaller change than first estimated.

### Finding F2 — Basiskorting value conflict (non-blocking; live mis-seed risk)

The PRD states basiskorting = **XCG 3,247.35/yr** ("official 2026"). Architecture **AD-13** and Story 1.5 use **XCG 2,915/yr**, and AD-13 explicitly states 3,247.35 is an *inkomstenbelasting* figure, "not the loonbelasting withholding basiskorting." The epics are correct per AD-13; the **PRD is wrong/stale**.

**Impact:** an implementer trusting the PRD could "correct" the Story 1.5 seed to 3,247.35 — a wrong value that would fail the acceptance criterion ("match official 2026 publications within XCG 0.02"). **Action:** correct the PRD to 2,915 (with the AD-13 note) to prevent mis-seeding. Not a gate.

### Finding F3 — Premium-base formula stale in PRD (non-blocking; resolved by AD-14)

PRD Steps 2 & 5 define the BVZ/AOV premium base as `total_loon − verwervingskosten − pension_emp [− beschikking]`. AD-14 redefines it as `BASIC + ALW`. The epics correctly follow AD-14. **Action:** update the PRD Step 2/5 text to the AD-14 base to avoid confusing implementers. (Pension — the one term not covered by an AD — is escalated separately as F1; beschikking's base-deduction role likewise lapses under AD-14, though beschikking survives as an employee field for Lei di Bion approval.)

### Finding F4 — `singleton` field on `hr.salary.rule` not explicit (minor)

PRD extends `hr.salary.rule` with a `singleton` boolean (controls whether a component may be applied more than once per employee). No story names it. Likely belongs in Story 1.7 or the apply wizard (1.8). **Action:** add an AC or confirm it is implied. Low severity.

## 4. UX Alignment

No standalone UX document exists — by design (the module uses standard Odoo list/form/menu screens). The UX requirements are captured as UX-DR001–004 in the epics and covered by Stories 1.2 (scoped theme + `.cw_theme_prl10n` wrapper, light/dark tokens, `i18n/nl.po`), 1.7/1.10 (own-screen wrapper), and 1.9 (extended Odoo views left unstyled). Portal styling (UX-DR004) is correctly deferred with OQ-01. **No UX gaps.**

## 5. Epic Quality Review

- **Value-oriented epics:** each epic delivers a coherent user outcome (config/foundation → correct payslip → run cycle → filings → vacation), not a technical milestone. ✓
- **No forward dependencies:** verified in the prior create-epics step-04; the two exclusion flags are defined in 2.1 so early base rules never depend on later routing stories. ✓
- **Dependency direction:** Epic 2 computes a single payslip independently of the batch; Epic 3 consumes Epic 2; Epic 4 reads Epic 3's closed run. Clean forward chain. ✓
- **Scope discipline:** Epic 5 (statutory vacation) is correctly labelled v1.1R and excluded from the v1.0R release. ✓
- **Bilingual parity:** EN and NL hold the same 38 stories with identical numbering. ✓

## 6. Final Assessment

**Verdict: READY** (updated 2026-07-04 after F1–F4 closure; the initial assessment was Conditionally Ready).

The epics and stories are internally consistent, fully cover the PRD's statutory sequence, lifecycle, accounting, reports, and security, and are correctly aligned to the (binding) Architecture Spine. One open **scope decision** must be made before sprint planning; two PRD reconciliations should be done to prevent mis-implementation.

| # | Finding | Severity | Gate? | Owner action |
|---|---|---|---|---|
| F1 | Employee pension contribution (`PENSION_EMP`) unmapped | **Blocking** | **Yes** | ✅ **CLOSED 2026-07-04** — premie-loon side resolved (not deductible; AD-14 correct); loonbelasting side IN SCOPE → Story 2.6 updated (EN+NL) |
| F2 | Basiskorting 3,247.35 (PRD) vs 2,915 (AD-13/epics) | Medium | No | ✅ **RESOLVED 2026-07-04** — PRD corrected to 2,915 (§Steps 8–10 and §Toeslagen table) with the AD-13 note |
| F3 | Premium-base formula stale in PRD | Low | No | ✅ **RESOLVED 2026-07-04** — PRD Steps 2 & 5 rewritten to the AD-14 `BASIC + ALW` base + AD-24 cumulative; pension left flagged as open F1 |
| F4 | `singleton` field on `hr.salary.rule` not explicit | Low | No | ✅ **RESOLVED 2026-07-04** — `singleton` AC added to Story 1.7 (EN + NL) |

**Recommendation:** All findings (F1–F4) are resolved. **Implementation-ready — proceed to `/bmad-sprint-planning`.**

