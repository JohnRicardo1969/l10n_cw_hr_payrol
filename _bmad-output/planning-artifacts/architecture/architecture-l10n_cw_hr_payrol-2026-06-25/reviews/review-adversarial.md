# Adversarial review — two AD-compliant units that still diverge

**Verdict:** Spine is strong but has two holes where independent builders obey every AD yet build incompatibly. Both are payroll-correctness critical.

## CRITICAL — AD-5 fixes *where* rates live but not the *read/representation contract*
`hr.tax.bracket` cleanly models a *progressive band table* (loonbelasting, bijzondere). But AD-5 now routes **flat premiums** (BVZ_ER 9.3%), **pure wage ceilings** (ZV/OV cap 85 753.20, BVZ cap 150 000), and **sliding scales** (BVZ 0–4.3% bands, AVBZ 29 897.44 threshold) through the same model. Two authors will diverge:
- Author A calls `compute_tax(base, 'bvz')` expecting the premium back; Author B `search()`es the bracket and multiplies `rate` manually.
- A ceiling has no natural representation as a tax *band* — is it the top band's `income_to`? a record with `rate=0`? a separate cap field?
- `compute_tax`'s shown body only does progressive accumulation; its docstring claims "other tax_types return the premium directly" but no branch implements that.

**Fix:** add the per-`tax_type` read contract to AD-5 (how flat / ceiling / sliding are each encoded as records and which call reads them). Without it, AD-5 is unenforceable.

## CRITICAL — AD-9 has no reopen / re-close semantics; PRD allows reopening closed runs
PRD grants Payroll Manager "reopening closed runs." AD-9 increments YTD and posts the journal *in* `action_close()`, with no reversal on reopen. Reopen → edit → close again ⇒ **YTD double-counted and a second journal posted.** Two builders diverge: one makes the YTD upsert idempotent per payslip; another blindly increments.

**Fix:** AD-9 must define reopen/recompute integrity — either YTD upsert is idempotent (keyed by payslip, set-not-increment, or store per-payslip contribution) and `action_close` reverses/replaces the prior `account.move`, or reopening is explicitly forbidden for v1.0R (contradicting the PRD — surface to user).

## MEDIUM — NONTAXED category & final-payable assembly undefined
`NONTAXED` (Seq 140) is "added to net" but runs *after* `NET` (Seq 130) and is not premium/tax-bearing. AD-2 says `NET = BASIC+ALW+DED`. Is NONTAXED in one of those categories (then NET would need to exclude it) or a separate post-NET line where payable = NET + NONTAXED? Authors diverge on the payslip's final payable.

**Fix:** state that NONTAXED is a separate post-NET line (own category, GL pass-through debit+credit), and the amount paid = NET + NONTAXED.
