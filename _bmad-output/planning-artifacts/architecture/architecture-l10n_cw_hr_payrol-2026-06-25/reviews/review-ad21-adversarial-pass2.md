# Adversarial re-review (pass 2) — AD-21 (Bijzondere beloningen tarief)

**Review pass:** 2026-06-27 — VALIDATE pass 2, AD-21 and its seams only. No spine modified; findings only.

**Scope.** Re-review of the revised AD-21 after the author reframed the tarief in response to pass-1 findings. This pass (a) confirms whether each pass-1 finding is closed against the *current* spine text, and (b) probes for new divergence introduced by the reframing. Seams assessed: AD-2, AD-4, AD-5, AD-9, AD-14, AD-20. The known-open spine-wide set (C-2 aov_aww_surcharge, C-3 basiskorting, H-1 the 0.465 literal, H-2 shared-ceiling ownership, H-4 BVZ/AVBZ sliding-scale source) is out of scope and not re-reported.

**Verdict:** PASS with two narrowed MEDIUM residuals. The reframing holds. Pass-1's CRITICAL order-dependence is **closed for the automatic path** — the tarief is now a pure function of prior-year/contract data and a manager override, and no jaarloon basis reads a current-year beloning payslip. The two new MEDIUM findings below are not a reopening of the CRITICAL; they are narrower seams that live **only on the manager-override path**, where the spine still leaves the override basis composition and the AD-9 write-semantics undefined.

## Per-prior-finding disposition

| Pass-1 # | Sev | Disposition | Basis |
| --- | --- | --- | --- |
| 1 | CRITICAL | **CLOSED** | Lines 350-358: tarief is a function only of prior-year jaarloon (A/B), `contract.wage × 12` (C), or manager override — "**never** a current-year beloning payslip amount." Earliest-dated selection removed. |
| 2 | HIGH | **CLOSED (moot)** | No earliest-dated payslip selection survives, so the missing date-field and tie-break can no longer bite. |
| 3 | HIGH | **PARTIALLY-CLOSED** | Three named sub-issues resolved by the line-level applied-rate mechanism (lines 366-371). The AD-9↔AD-21 write-semantics seam persists in narrowed form on the override path — see NEW-2. |
| 4 | HIGH | **CLOSED** | Lines 380-381: TAX_INC rule (Seq 80) named as owner of the exclusion via a bijzondere-beloning category marker; line 390 confirms it "holds either way." |
| 5 | HIGH | **CORRECTLY-PARKED / visibly flagged** | Line 385 carries an explicit `[OPEN — pending statutory confirmation]` for the SVB premium base. Visible deferral to the product owner, not a spine defect. |
| 6 | MEDIUM | **PARTIALLY-CLOSED** | Lines 347-349 give a default ("annual regular taxable loon … excluding the bijzondere beloningen themselves," prior-year YTD) but still do not name *which* YTD rule(s) compose it. |
| 7 (band-edge) | MEDIUM | **CLOSED** | Line 112: band match is `income_from ≤ jaarloon < income_to`, top band `income_to = 0` uncapped, matching the table's *"groter of gelijk aan … maar kleiner dan"*. |
| 8 | LOW | **OPEN** | AD-5 (lines 115-117) still states the `compute_tax` prohibition as prose only — no fail-loud guard. The Consistency-Conventions row (line 409) still associates bijzondere rates with the general `compute_tax()` read pattern. Skim-the-table misuse remains reachable. |
| 9 | LOW | **PARTIALLY-CLOSED (clarity nit persists)** | AD-4's scoping sentence (line 85, "applies only to SVB premium ceilings and thresholds") already excludes the `bijzondere_beloning` bracket, so a careful reader will not annualise. But AD-4's Binds line (line 79, "every rule applying a … bracket") vs that scoping sentence remain in mild tension; EXTRA_TAX is not added to AD-4's exception note. Not a live divergence. |

## Verification detail of the claimed fixes

**Findings 1 & 2 — order-dependence and earliest-dated ambiguity.**
Verified the central claim against every basis: does any jaarloon basis read a current-year payslip amount? It does not.

- Case A (whole prior year): actual prior-year jaarloon (prior-year YTD) — prior-year data.
- Case B (part prior year): that wage annualised — prior-year data.
- Case C (joined this year): `contract.wage × 12` (line 352) — config, not a payslip.
- Manager override: the current-year jaarloon entered by the manager (lines 345-346, 352) — config; line 352 explicitly excludes "a current-year beloning payslip amount."

Line 356 states the supersession in terms: the value is "fixed by prior-year/contract data, not by a payslip, so the YTD-style ownership rule is neither needed nor correct here." The pass-1 CRITICAL (a posted withholding ordered by which beloning closes first) cannot occur on the automatic path: the rate is identical regardless of close order. The invalid YTD analogy that pass-1 attacked has been removed and replaced with the correct framing (the value is order-independent because it never reads a current-year payslip — not because it is an idempotent sum). **Genuinely closed.**

**Finding 3 — read precedence and AD-9 collision.**
The three sub-issues pass-1 raised are resolved:

- *Record-present-vs-live precedence:* line 359-361 — "read if present; otherwise the rule computes the default and the record is persisted at `action_close()`." Unambiguous.
- *Annual-freeze-vs-overridable collision:* resolved by the line-level applied-rate mechanism (lines 366-371). The (employee, year) record is the carry-forward default; the **line-level applied rate** is the audit truth of what was withheld. The two no longer compete.
- *Reopen-and-edit-earliest:* line 370-371 — "a manager changing the override later cannot retroactively alter an already-posted withholding"; reconciliation is via the IB return. Posted withholdings are frozen on the line.

The "later payslips never redefine it" clause that collided with AD-9's upsert has been removed (superseded by line 356). However, the write-semantics seam is not fully retired — see NEW-2.

**Finding 4 — TAX_INC exclusion owner.**
An owner is now named: lines 380-381 designate the TAX_INC rule (Seq 80) as the named owner of the exclusion, keyed off a "bijzondere-beloning category marker." Line 390 confirms the exclusion owner "holds either way" regardless of how the open premium-base question resolves. Owner exists; finding closed. (The category-marker mechanism is described at spine altitude only, which is appropriate; the marker's field-level shape is seed.)

**Finding 5 — premium base.**
Line 385 flags the SVB premium-base question with an explicit `[OPEN — pending statutory confirmation]` tag, and lines 386-392 spell out both branches (in-`ALW` vs own-category) and note the `TAX_INC` exclusion owner holds either way. The deferral is visible and correctly parked with the product owner — treated here as not-a-defect, consistent with the AD-14 overtime precedent.

**Band-edge (Finding 7).**
Confirmed at line 112: `income_from ≤ jaarloon < income_to`, with `income_to = 0` as the uncapped top band and the parenthetical matching the table's Dutch wording. This is the half-open convention pass-1's fix direction requested; band boundaries are now deterministic.

## NEW findings (introduced or left by the reframing)

Both live on the **manager-override path**. The automatic path is airtight; these are why the order-independence claim is not yet airtight in full generality.

### NEW-1 — MEDIUM — Override "current-year jaarloon" has no pinned composition; the *controleren* surfaced figure is undefined

**Units in conflict:** two EXTRA_TAX / override-basis implementors.

Lines 345-349 defer jaarloon composition to seed/tech-design. Line 352 protects only against reading "a current-year **beloning** payslip amount." Neither pins how the **override** "current-year jaarloon" is composed. An implementor who computes the override basis as current-year *regular* wage accumulated to date (YTD-to-date) is fully compliant with line 352 — it reads no beloning — yet the value is **time-dependent**: the same override applied at different points in the year lands in a different band, yielding a different posted withholding. The "current-year jaarloon surfaced for the *controleren* check" (line 362) has the identical undefined-computation hole: nothing says whether the surfaced figure is `contract.wage × 12` (order-independent) or accumulated current-year earnings (order-dependent).

This is the precise seam that keeps the order-independence guarantee from being airtight: the automatic bases are pinned, but the override basis — which directly selects the band — is not.

**Fix direction (not prescriptive):** pin the override "current-year jaarloon" to an order-independent composition (e.g. `contract.wage × 12`, the same as Case C), and define the surfaced *controleren* figure the same way, so neither depends on how much has been paid year-to-date.

### NEW-2 — MEDIUM — AD-9 "upsert" vs AD-21 "read-if-present-else-persist" collide under override (narrowed form of pass-1 Finding 3)

**Units in conflict:** `action_close()` write-path implementor / EXTRA_TAX default-read implementor.

AD-9 line 160 says every close **upserts** the (employee, year) tarief record. AD-21 lines 359-362 say the rule computes and **persists only when the record is absent**, then the value "carries forward as the default … overridable at any payout." For the automatic value these are reconcilable (re-upsert writes the same pure-function value, harmless). They diverge under override:

- Beloning 1 closes → record persisted at, say, 15%.
- Beloning 2: manager overrides to 20%; the line records 20% as applied (correct, per lines 366-371).
- At beloning 2's close, AD-9 says *upsert the record*. Does the upsert rewrite the (employee, year) record to 20% (so beloning 3 defaults to 20%), or is the 20% payout-local (so beloning 3 defaults back to 15%)?

The spine does not disambiguate, so two compliant implementors produce different **beloning-3** default withholding. This is the same AD-9↔AD-21 write-semantics seam pass-1 Finding 3 named, reincarnated for the override case after the earliest-dated clause was removed. It does **not** reopen the CRITICAL (no posted withholding is retroactively altered — the line-level applied rate is frozen), but it leaves the carry-forward default ambiguous.

**Fix direction:** state whether a per-payout override (a) updates the (employee, year) carry-forward default for subsequent payouts, or (b) is payout-local and leaves the default intact; and reconcile AD-9's "upsert" wording with AD-21's "persist only when absent" (e.g. AD-9 inserts-if-absent and only the explicit override path may update).

## Items unchanged from pass-1 (still open, low priority)

- **Finding 8 (LOW, OPEN):** the `compute_tax`-must-not-be-used prohibition for `bijzondere_beloning` is still documentation-only (AD-5 lines 115-117); a fail-loud guard would enforce it. The Consistency-Conventions row (line 409) still routes bijzondere rates through the general `compute_tax()` description.
- **Finding 9 (LOW, clarity nit):** AD-4's Binds line ("every rule applying a … bracket") vs its scoping sentence ("only SVB premium ceilings and thresholds") remain in mild tension for the one `bijzondere_beloning` bracket; EXTRA_TAX is not named in AD-4's exception note. No live divergence.
- **Finding 6 (MEDIUM, PARTIALLY-CLOSED):** a default jaarloon composition is now stated ("annual regular taxable loon … excluding the bijzondere beloningen themselves," prior-year YTD), but the specific YTD rule(s) that compose it are still unnamed; "regular taxable loon" admits a TAX_INC-base vs gross reading.

## Summary

The author's reframing is a sound fix to the pass-1 CRITICAL: binding the tarief to prior-year/contract data and a manager override — and removing the earliest-dated-payslip selection — eliminates close-order dependence on the automatic path, and the line-level applied-rate mechanism cleanly closes the freeze/override/reopen sub-issues. The TAX_INC exclusion now has a named owner, the band-edge convention is pinned, and the premium-base question is visibly parked. The two residual MEDIUM seams (NEW-1, NEW-2) are confined to the manager-override path: the override basis composition and the AD-9/AD-21 write-semantics under override are still undefined, and pinning both would make the order-independence guarantee airtight end-to-end.
