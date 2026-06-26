# Rubric walker + compliance/data-integrity lens

**Verdict:** Covers the divergence points and the PRD capabilities; operational envelope is placed, not silent. Two carry-overs from the adversarial review are the only real gaps.

## Good-spine checklist
- Fixes real divergence points for the level below (rules, models, reports): ✔ — sign, category, sequence, annualisation, gating, layer boundaries.
- Every AD's Rule enforceable & prevents its divergence: ✔ except **AD-5** (read contract gap — see adversarial CRITICAL) and **AD-9** (reopen gap — see adversarial CRITICAL).
- Nothing under Deferred lets two units diverge: ✔ — deferred items are onboarding/data/out-of-scope, not structural.
- Named tech verified-current: ✔ (see verification review).
- Brownfield ratify: N/A (greenfield).
- Spec/PRD capability coverage: ✔ — Capability→Architecture map covers all PRD areas.
- Every owned dimension decided/deferred/open: ✔ — operational envelope deferred to Odoo.sh explicitly.

## Compliance / data-integrity lens (regulated statutory payroll)
- **Audit trail**: `mail.thread` on all custom models + append-only rates (AD-5) — strong. ✔
- **Least privilege & data protection** (Landsverordening bescherming persoonsgegevens): four groups + employee record rule captured in conventions. ✔
- **Reconstructability of prior periods**: append-only dated rates (AD-5) enable correct recompute of historical payslips. ✔
- **GAP (data integrity)**: reopen/re-close double-posting (adversarial CRITICAL on AD-9) is the single biggest integrity risk for a statutory ledger — must be closed.
- **GAP (low)**: AD-12 sets per-rule round-to-2dp; confirm no compounding rounding error across the chain vs the XCG 0.02 acceptance tolerance. Acceptable as stated; note for test design.

## Tail (low, deferred to detailed design)
- NONTAXED category placement (adversarial MEDIUM) — fix in spine.
- Rounding-accumulation test coverage — belongs in QA, not the spine.
