# Rubric-walker review — ARCHITECTURE-SPINE.md (v2, 2026-06-27)

**Run type:** VALIDATE — spine not modified; findings only.

**Gate verdict:** PASS with minor gaps. The spine is ready as a build substrate for independent
implementers. All three prior gate CRITICALs (AD-5 read-contract gap, AD-9 double-post on reopen,
NONTAXED category placement) are resolved. Four residual findings remain; none is blocking.

## Good-spine checklist

### 1. Fixes the real divergence points for the level below — PASS

All 20 ADs address divergence points for independently-built salary rules, models, and reports:
sign convention (AD-1), category assignment (AD-2), sequence discipline (AD-3), annualisation
(AD-4), dated-rate authority with full per-type read/representation contract (AD-5), enable/disable
gate and never-gate set (AD-6), active/enabled split (AD-7), three-tier decoupling (AD-8), single
state-commit point with idempotent YTD and controlled reopen (AD-9), accounting balance (AD-10),
layer boundaries (AD-11), money/rounding including declaration truncation (AD-12), statutory defaults
unconditional (AD-13), canonical premium base (AD-14), scoped theming (AD-15), distribution gate
(AD-16), effective date (AD-17), fail-loud on missing data (AD-18), company scoping (AD-19),
loonbelasting table model (AD-20).

Prior CRITICAL — AD-5 read/representation contract: RESOLVED. The current spine includes explicit
per-tax_type contracts (progressive: band-by-band accumulation; flat-with-ceiling: one dated record,
cap at income_to, apply rate; sliding: multiple band records, select by annualised base).

Prior CRITICAL — AD-9 reopen/re-close integrity: RESOLVED. The current spine defines idempotent
YTD (recompute as sum over year's confirmed payslip lines, not blind increment) and specifies that
reopen reverses the posted account.move.

Prior MEDIUM — NONTAXED category placement: RESOLVED. AD-2 now clarifies that NONTAXED is a
separate post-NET line in its own category, functions as a GL pass-through (employer-cost debit +
payable credit), and that the amount paid to the employee is NET + NONTAXED.

### 2. Every AD's Rule is enforceable and prevents its stated divergence — PASS with two notes

All ADs are enforceable as stated, with the following two low-severity notes:

**[LOW] AD-9: payslip confirmation state during reopen is undefined.**
AD-9 specifies that on close, `ytd_amount` is set to the sum over the year's *confirmed* payslip
lines. It also specifies that reopen reverses the `account.move`. What it does not specify is
whether the run's payslips are de-confirmed (unlocked) during reopen. Two builders could diverge:

- Builder A unlocks payslips on reopen, meaning they fall out of the "confirmed" pool until
  re-close relocks them. The recompute window is open.
- Builder B keeps payslips in a confirmed state during reopen and only relocks on re-close. The
  idempotent YTD sum still produces the correct result, but the payslip edit window is different.

The idempotent YTD logic likely makes both implementations produce the same YTD figure on re-close,
but the payslip-editing window (what the Payroll Manager can change between reopen and re-close)
differs. Define payslip state on reopen (return to `draft` or to a dedicated `reopened` state).

**[LOW] Lifecycle diagram omits the Close → Verify reopen arc.**
The `stateDiagram-v2` shows `Close --> [*]` as a terminal state. AD-9 describes a controlled reopen
path. An implementer reading only the diagram may not build the reopen transition. Add:
`Close --> Verify : action_reopen() — reverse journal`.

### 3. Nothing under Deferred could let two units diverge — PASS

Every deferred item is one of: a distribution channel/medium (gate is fixed by AD-16), a data
content parameter (overtime default rates, GL account numbers), an onboarding configuration, or a
platform concern. None is structural.

OQ-07 (SVB gevarenklasse interim `l10n_cw_ov_percentage` Float on contract) is needed for the v1.0R
OV rule but is named in the Deferred entry, and field-level shape is owned by the tech design
(which the spine explicitly delegates). No divergence risk at this altitude.

### 4. Named technology verified-current — PASS with one finding

The memlog records explicit verification of the Odoo 19 salary-rule execution context. Odoo 19
Enterprise / Odoo.sh is current. SCSS registration via the manifest `assets` key under
`web.assets_backend` is current Odoo practice (Odoo 16+). The `countries: ['cw']` manifest key is
flagged for impl-time confirmation in the verification review. No technology assertion rests on
unverified training data.

**[MEDIUM] AD-20 contains a statutory rate literal that violates AD-5.**
AD-20 specifies the above-ceiling formula as:
`ceiling_tax + (TAX_INC − ceiling_wage) × 0.465`

The `0.465` is a statutory rate from MR 144 § Algemeen (the top marginal rate for the loonbelasting
withholding). Under AD-5, no statutory rate should be a literal in rule Python. The spine therefore
contains an internal contradiction. Two builders diverge:

- Builder A reads AD-20 and hardcodes `0.465` in the salary rule.
- Builder B reads AD-5 ("no literal") and creates an `above_ceiling_rate` field on the
  `hr.loonbelasting.tabel` header to make it data-driven.

Recommended resolution (either is acceptable; pick one and add to AD-20):

Option 1 — data-driven: add `above_ceiling_rate = fields.Float` to the `hr.loonbelasting.tabel`
header model; seed it to `0.465` for 2026; `lookup_loonbelasting` returns it alongside the
`ceiling_tax` and `ceiling_wage`. Future rate changes update the header, not the rule.

Option 2 — named carve-out: explicitly state in AD-20 that `0.465` is a named exception to AD-5
by analogy with the loonbelasting-as-AD-4-exception, declare its source (MR 144 § Algemeen), and
require that a code deploy accompanies any future change (with rationale: top rate changes are
extremely rare, full-table replacement is the normal delivery vehicle for regulatory changes).

### 5. Ratifies brownfield codebase conventions — N/A (greenfield)

### 6. Covers the spec/PRD's capabilities — PASS with one note

The Capability → Architecture Map covers all PRD areas: statutory calculation engine, SVB premium
rate management, loonbelasting table lookup + annual upload, three-tier wage component model,
per-employee exemptions, YTD accumulation, run lifecycle, accounting integration, declarations,
payslip PDF, backend UI theming, security. Bijzondere beloningen falls under the calculation engine
(EXTRA_TAX rule, `bijzondere_beloning` tax_type in AD-5).

**[LOW] The bijzondere beloningen 6-band statutory correction is in the memlog only, not in the spine.**
The memlog records a data correction: the official 2026 Belastingdienst publication shows 6 rate
bands; tech design v3.0D listed only 5 (the 30 % band for XCG 86,900–123,100 is missing). An
implementer who reads the spine and tech design v3.0D but not the official PDF or the memlog will
produce incorrect seed data for the `bijzondere_beloning` type in `hr.tax.bracket`.

The correct 6 bands (from the official 2026 publication) are:
`0 → 9.75 %, 43,500 → 15 %, 58,000 → 23 %, 86,900 → 30 %, 123,100 → 37.5 %, 181,000 → 46.5 %`

The spine should document this in the AD-5 `bijzondere_beloning` progressive read-contract section
or in Consistency Conventions under "Statutory data," explicitly noting that v3.0D had an error
and the official 2026 Belastingdienst publication is authoritative.

### 7. No new AD weakens or contradicts a parent spine — N/A (`binds: []`)

No parent spine; all 20 ADs are internally consistent. No mutual contradictions found beyond
the AD-5 / AD-20 literal conflict reported in finding 4 above.

### 8. Every dimension at this altitude is decided, deferred, or an open question — PASS

Operational/environmental envelope: explicitly deferred ("Owned by the Odoo.sh platform, not module
code; no module-level decision needed"). No silent gap.

Security model: four groups, least-privilege, employee record rule, distribution gate (AD-16),
documented in conventions. ✔

Schema migration: migration discipline (ship Odoo migration scripts, never destructively drop
historical records) documented in Consistency Conventions. ✔

Multi-company enablement: explicitly open; safe either way due to AD-19 scoping. ✔

Reopen / herberekening path: defined in AD-9 (with the payslip-state caveat above). ✔

### 9. Deferred items are genuinely non-blocking — PASS

All deferred items are v1.1R+ features, onboarding config, or platform concerns. No deferred item
can cause two v1.0R implementation units to diverge on statutory correctness.

## Compliance / data-integrity lens (regulated statutory payroll)

- **Audit trail:** `mail.thread` on all custom models + append-only rates (AD-5) + append-only table
  rows (AD-20). Strong. ✔
- **Reconstructability of prior periods:** Dated rates (AD-5) + versioned loonbelasting tables (AD-20)
  + canonical effective date (AD-17) together guarantee that a historical recompute reproduces the
  exact rates and table in force for the original period. ✔
- **Data integrity on reopen:** Idempotent YTD (sum-not-increment, AD-9) + account.move reversal
  prevents double-counting and duplicate postings. The AD-9 payslip-state gap is low risk because
  the YTD sum formula is idempotent regardless of which path is taken; the difference is operational
  (edit window), not statutory correctness.
- **Privacy / data protection:** Company-scoped operational data + record rules (AD-19) + four-group
  least-privilege model in conventions. ✔
- **Fail-loud integrity:** AD-18 prevents silent zero-tax on missing statutory data, which is the
  regulatory compliance risk in a statutory withholding system. ✔

## Summary of findings by severity

| Severity | Finding | Affected AD(s) | Recommended action |
|---|---|---|---|
| MEDIUM | AD-20 specifies `0.465` literal — violates AD-5 "no statutory rate as literal" | AD-5, AD-20 | Add `above_ceiling_rate` field to `hr.loonbelasting.tabel` header (option 1) or add named carve-out with update policy (option 2) |
| LOW | Bijzondere beloningen 6-band fix (30 % band missing in v3.0D) is not in the spine | AD-5 | Add the 6 correct bands to the AD-5 `bijzondere_beloning` section or Conventions |
| LOW | Lifecycle diagram omits the Close → Verify (reopen) arc defined in AD-9 | AD-9 | Add `Close --> Verify : action_reopen()` to stateDiagram-v2 |
| LOW | AD-9 does not specify payslip confirmation state during reopen | AD-9 | State explicitly whether payslips return to draft (or a reopened state) on reopen |

All prior CRITICAL and MEDIUM findings (AD-5 read contract, AD-9 double-post, NONTAXED placement)
are resolved in the current spine (v2, 2026-06-27).
