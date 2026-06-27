# Adversarial review — AD-21 (Bijzondere beloningen tarief)

**Review pass:** 2026-06-27 — VALIDATE pass, AD-21 and its seams only. No spine modified; findings only.

**Scope note.** This pass attacks **only** AD-21 (Seq ~110 EXTRA_TAX + the per-(employee, year) `hr.employee.bijzonder.tarief` record) and its seams with AD-2, AD-4, AD-5, AD-9, AD-14, AD-20. The known-open findings C-2 (aov_aww_surcharge 6× miscompute), C-3 (basiskorting 2 915 vs ~3 247), H-1 (the 0.465 literal in AD-20), H-2 (shared-ceiling ownership), and H-4 (BVZ/AVBZ sliding-scale source) are **out of scope and not re-reported**.

**Verdict:** FAIL / blocking. AD-21's central determinism claim — "the tarief is a pure function of the earliest-dated bijzondere-beloning payslip, like the idempotent YTD" — does **not** hold the way YTD's does: the tarief feeds a *posted* withholding, so the year's withholding is order-dependent even when the record value eventually converges. Around that core, four more seams let two AD-compliant implementors build incompatibly or withhold wrong tax.

**Supersession note.** The prior adversarial review's HIGH "EXTRA_TAX marginal-rate base: `TOTAL_LOON` vs full category sum" is **superseded** by AD-21, which now binds the rate to the employee's *jaarloon* (via `lookup_marginal_rate`), not a monthly base × 12. Its residual hole is no longer "which monthly base" but "what is jaarloon" — Finding 6 below. It is not re-reported as the old finding.

## Findings summary

| # | Severity | Seam | One-line |
| --- | --- | --- | --- |
| 1 | CRITICAL | AD-21 ↔ AD-9 | "Earliest defines" is not order-independent the way YTD is; out-of-order close posts the year's beloningen at inconsistent rates. |
| 2 | HIGH | AD-21 | "Earliest-dated" names no date field and has no same-date tie-break (AD-20 has one; AD-21 doesn't). |
| 3 | HIGH | AD-21 ↔ AD-9 | Record-present-vs-live precedence undefined; "annual freeze / later only reads" collides with "default, not lock / overridable"; reopen-and-edit-earliest has no defined outcome. |
| 4 | HIGH | AD-21 ↔ AD-2 | "Excluded from TAX_INC" has no named enforcement; AD-2 has no in-NET / out-of-TAX_INC category slot, so double- or zero-withholding is reachable. |
| 5 | HIGH | AD-21 ↔ AD-14 ↔ AD-2 | Whether bijzondere beloningen (incl. incidentele overuren) stay in `ALW` — and so attract SVB premiums per AD-14 — is undefined. |
| 6 | MEDIUM | AD-21 | "Which components count toward jaarloon" is deferred, but jaarloon *is* the rate selector; "read prior-year YTD" never says YTD of which rule(s). |
| 7 | MEDIUM | AD-21 ↔ AD-5 | `lookup_marginal_rate` band-edge inclusivity (`[from,to)` vs `(from,to]`) is undefined; a jaarloon on a band boundary picks two rates. |
| 8 | LOW | AD-5 | `lookup_marginal_rate`-only rule for `bijzondere_beloning` is documentation-only; nothing stops a `compute_tax` call. |
| 9 | LOW | AD-21 ↔ AD-4 | EXTRA_TAX's non-annualisation is correct but only implicit; AD-4's Binds line vs its scoping sentence are in mild tension for this one bracket. |

## CRITICAL — "Earliest defines, later reads" is not order-independent the way idempotent YTD is; out-of-order close withholds the year's beloningen at inconsistent rates

**Units in conflict:** `action_close()` implementor (writes the tarief record, AD-9) / EXTRA_TAX (Seq ~110) implementor (reads it).

AD-21 (line 349–351): the tarief is *"a pure function of the earliest-dated bijzondere-beloning payslip in that year … Like the idempotent YTD (AD-9), the value is therefore independent of close order and reproduces exactly on reopen/recompute."*

The analogy is **invalid**, and the reason is precise. YTD is order-independent because it is (a) a **commutative sum**, (b) **recomputed over the full confirmed set at every close** (AD-9 line 163–168), and critically (c) **nothing already posted depends on a later recompute** — each payslip's own NET/withholding is computed at *its* close from data available then, and a later month re-summing YTD never reaches back into an already-posted month.

The tarief breaks (c). It is a **selection-of-earliest that feeds a posted withholding**. Trace the out-of-order close the prompt names:

1. A December bonus run is closed **first** (the March vakantiegeld run does not yet exist, or is still draft). At December's `action_close()`, the only confirmed beloning payslip is December, so the record is written from December's basis/jaarloon. EXTRA_TAX on the December slip withholds at that rate, and that amount is **posted to the journal and locked** (AD-9).
2. The March run (earlier `date_to`) is later created, computed, and closed. Now the *earliest-dated* confirmed beloning is March. Two compliant `action_close()` implementors diverge, and **both readings fail AD-21**:
   - **Recompute-over-full-set (the YTD analogy taken literally):** March's close re-derives the record from the earliest-dated payslip → the record flips to March's basis/rate. But December already posted at the old rate and is locked. The **year now contains two different bijzondere-beloningen rates**, and the record no longer matches December's posted withholding. Reproducibility is broken in the exact dimension AD-21 promised.
   - **First-writer-wins ("later beloningen never redefine it"):** the record keeps December's value. But December is *not* the earliest-dated payslip — so the record violates AD-21's own definition ("a pure function of the **earliest-dated** … payslip").

Either way, the determinism claim is false under out-of-order close. The harder, unrebuttable form: even if the *record value* eventually converges, **the year's posted withholding is order-dependent**, because EXTRA_TAX on the earlier-closed-but-later-dated slip already withheld at a rate the final record contradicts. "The record is deterministic" does not rescue this; a payslip was posted with a rate the spine now says is wrong, and AD-9's reopen is a manual, operator-initiated path — there is no cascading recompute of sibling beloning payslips when the earliest changes.

**Why it matters:** This is the headline guarantee of AD-21. As written it holds only when beloning payslips are closed in date order and the earliest is closed first — a sequencing assumption the spine neither states nor enforces (and which off-cycle bonus runs routinely violate).

**Fix direction (not prescriptive):** AD-21 must either (a) require that the (employee, year) tarief be **established before any beloning is withheld** — e.g. computed/frozen on a defined trigger independent of close order, with later beloning payslips blocked or warned if the earliest-dated one is not yet the source — or (b) make EXTRA_TAX withholding explicitly provisional and require a cascading recompute of all that year's open beloning payslips whenever the earliest changes, with the residual settled via the Aangifte IB (which the Scope-exclusion clause already contemplates). The YTD analogy should be dropped; YTD is a passive accumulator, the tarief is an input to a committed number.

## HIGH — "Earliest-dated" names no date field and has no same-date tie-break

**Units in conflict:** two `action_close()` / tarief-selection implementors.

AD-21 selects "the earliest-dated bijzondere-beloning payslip in that year" but never says **which date** orders the selection. An Odoo payslip carries `date_from`, `date_to`, and a `date` (payment date). AD-17 makes `payslip.date_to` the canonical *effective date for rate lookups*, but that is a statement about which rates apply, not about which payslip is "earliest"; an implementor may equally read "earliest-dated" as ordering by `date_from` or by payment `date`. Two implementors pick different fields → for any employee whose beloning runs straddle a period boundary, a different payslip is "earliest" → different basis choice → different frozen rate.

Worse, **there is no tie-break for equal dates.** The realistic case is two runs in the same month — a regular monthly run carrying vakantiegeld and a separate off-cycle bonus run — both with month-end `date_to`. "Earliest-dated" is then a tie, and the manager's basis/override choice may differ between the two slips, so the chosen rate differs by which slip an implementor treats as earliest. AD-20 hit exactly this class of problem and resolved it explicitly with `valid_from desc, id desc` (lines 300–302); AD-21 ships no equivalent. Two seeders/implementors obeying AD-21 to the letter produce different rates.

**Fix direction:** name the ordering field (presumably `date_to` for consistency with AD-17) and add a deterministic tie-break (e.g. lowest `id`) for equal dates, mirroring AD-20.

## HIGH — Record-present-vs-live precedence is undefined; "annual freeze" collides with "default, not lock," and reopen-and-edit-earliest has no defined outcome

**Units in conflict:** two EXTRA_TAX implementors (read path) / `action_close()` implementor (write path).

AD-21 carries two clauses that an implementor must reconcile and the spine never does:

- **Annual freeze (lines 349–351):** "the earliest beloning **defines** the rate; every later beloning that year **reads** it and **never redefines** it."
- **Default, not lock (lines 353–354):** "The frozen rate is carried forward as the **default** … but stays **overridable at any payout**."

These are reconcilable only by reading "the record is never redefined, but the rate *applied at a given payout* may be locally overridden without rewriting the record." That reading is plausible — but it is **one of at least two**, and the spine states neither:

- **Implementor A — record is authoritative:** EXTRA_TAX, when the (employee, year) record is present, applies `record.rate` and ignores any later per-payout edit (honoring "later beloningen never redefine / only read").
- **Implementor B — live input is authoritative:** EXTRA_TAX always reads the payslip's basis/override input (the record only *pre-fills* it as a default per "Purity (narrow)", lines 356–358), so a later-payout override changes the withheld rate (honoring "overridable at any payout").

They diverge whenever a later payout is overridden, and they also diverge **at the very first beloning before the record exists**: the prompt's "read the record if present, else compute live" is the intended behaviour but is **never written down**. AD-21 only says EXTRA_TAX "may read the … tarief record **and** the manager's pre-close basis/override input" (Conventions, line 383) — it lists both sources without a precedence rule.

The sharp concrete failure is **reopen-and-edit-earliest.** The earliest beloning closes (record written, AD-9). The manager later reopens that earliest payslip and corrects its basis (e.g. switches from prior-year to current-year jaarloon because the prior year was unrepresentative — exactly the *"controleren"* override the source recommends). On re-close:
- Under Implementor A, the corrected basis is **silently ignored** for every later payout that reads `record.rate` — unless the re-close also rewrites the record, which collides with "later beloningen never redefine it" and is nowhere stated to be the earliest's privilege.
- Under Implementor B, the correction takes effect but the record must be rewritten, and AD-9 (close upserts the record) does not say **with what value** — the reopened-earliest payslip's basis, or the current closing payslip's.

The unanswered question that pins this: **does every `action_close()` upsert the (employee, year) record, and with which value?** AD-9 (line 158–160) says close upserts it; AD-21 says later payslips never redefine it. For any close other than the earliest's, those two collide and the spine gives no rule.

**Fix direction:** state EXTRA_TAX's read precedence as a single sentence ("if the (employee, year) record exists, EXTRA_TAX applies its rate; otherwise it computes live from the earliest beloning's basis input"), define whether a per-payout override writes anywhere or is payout-local, and specify which close (only the earliest's? any reopen of the earliest?) may (re)write the record.

## HIGH — "Excluded from TAX_INC" has no named enforcer, and AD-2 has no in-NET / out-of-TAX_INC category slot

**Units in conflict:** two implementors of the wage-component routing (TAX_INC composition vs EXTRA_TAX's beloning selector) — **not** two managers. The "the manager routes it by component choice" clause (line 363–364) deflects to a human, but the divergence is between the two engineers who build *what a component choice does*.

AD-21 (line 359–362) asserts a three-part invariant: each earning is withheld by **exactly one** route, bijzondere beloningen are **excluded from `TAX_INC`**, and **no amount is taxed by both** (and, implied, none by neither). Nothing in the spine **enforces** it. AD-2 enumerates the categories — `BASIC`, `ALW`, `DED`, `ER`, `NONTAXED` — and fixes `NET = BASIC + ALW + DED`. A bijzondere beloning (vakantiegeld, bonus) **must be in NET** (it is paid to the employee and is taxable), and AD-2 offers only `BASIC`/`ALW`/`DED` as in-NET homes. But the income that feeds `TAX_INC` is built from those same categories. **AD-2 has no slot that is simultaneously in-NET and out-of-`TAX_INC`** — which is exactly what a bijzondere beloning needs. The spine never defines `TAX_INC`'s category composition (it is seed), nor the mechanism that pulls a bijzondere amount out of it.

So two AD-2- and AD-21-compliant implementors:

- **Implementor A** puts vakantiegeld in `ALW` (natural: it is an allowance) and builds `TAX_INC` from `BASIC + ALW`. The amount lands in `TAX_INC` (maandtabel) **and** is selected by EXTRA_TAX → **double-withheld**, unless A special-cases a subtraction in `TAX_INC` that the spine never mandates.
- **Implementor B** invents a new category (e.g. `BIJZ`) for bijzondere earnings, keeps it in NET, and excludes it from `TAX_INC`. Correct — but B has unilaterally extended AD-2's closed category list, and A's build and B's build are incompatible.

A third route — putting it in a category that is in neither `TAX_INC` nor EXTRA_TAX's selector — yields **zero withholding**. All three obey AD-2 (a category is assigned) and AD-21 (the prose is honored); only the unwritten mechanism distinguishes them.

**Fix direction:** AD-21 (or AD-2) must name the single mechanism that *both* keeps a bijzondere earning in NET and excludes it from `TAX_INC` and routes it into EXTRA_TAX — e.g. a dedicated category, or a boolean on the component that TAX_INC and EXTRA_TAX both key off — and name who owns the exclusion. This shares a root with Finding 5 (undefined category placement of bijzondere earnings); the fixes should be designed together.

## HIGH — Premium-base inclusion of bijzondere beloningen (incl. incidentele overuren) is undefined at the AD-14 / AD-2 / AD-21 seam

**Units in conflict:** EXTRA_TAX / bijzondere-routing implementor / `BVZ_PREM_INC` (Seq 20) + `AOV_PREM_INC` (Seq 50) implementor.

AD-2 (line 68): "**All** overtime contributes to `ALW`." AD-14 (line 218–221): premium bases derive from `categories.BASIC + categories.ALW`, **overtime included**, "so all bases stay mutually consistent." AD-21 (line 332, 363): **incidentele overuren** is a bijzondere beloning, withheld via EXTRA_TAX and **excluded from `TAX_INC`**.

The seam: AD-21 carves incidentele overuren (and vakantiegeld, bonus) out of the *loonbelasting* income, but says **nothing about the SVB premium base**. Two readings, both compliant:

- If a bijzondere earning **stays in `categories.ALW`** (required by AD-2 for overtime; natural for an allowance), then by AD-14 it **is in the SVB premium base** — incidentele overuren and vakantiegeld attract AOV/AWW/AVBZ/BVZ premiums.
- If the Finding-4 fix moves bijzondere earnings into a **separate category** to get them out of `TAX_INC`, they fall **out of `categories.BASIC + categories.ALW`** and therefore **out of the premium base** — premiums no longer apply.

These produce **materially different premium liability** for the same employee, and the spine does not say which is intended. The statutory answer (do Curaçao SVB premiums attach to vakantiegeld / incidentele overuren?) is not stated; AD-14's "overtime included" was resolved for the *premium* base in the regular-overtime context (line 222–224), but AD-21 introduces a *second* kind of overtime (incidenteel) whose premium treatment AD-14 never contemplated. The Finding-4 mechanism choice and this premium-base outcome are entangled: fixing the TAX_INC exclusion by re-categorizing silently changes premium liability.

**Fix direction:** state explicitly whether bijzondere beloningen are in the SVB premium base, and reconcile with AD-2 ("all overtime → ALW") and AD-14 ("ALW → premium base"). If incidentele overuren is premium-bearing but tax-via-table, the category mechanism from Finding 4 must keep it in the premium base while excluding it from `TAX_INC` — i.e. the exclusion must be `TAX_INC`-specific, not a blanket move out of `ALW`.

## MEDIUM — Jaarloon composition is deferred, but jaarloon *is* the rate selector; "read prior-year YTD" never says YTD of which rule(s)

**Units in conflict:** two EXTRA_TAX / jaarloon-derivation implementors.

AD-21 (Scope exclusion / detailed-design handoff) leaves "which components count toward jaarloon" to detailed design. For most quantities that would be an acceptable seed-level deferral. Here it is not, because **jaarloon is the band selector** (`lookup_marginal_rate(jaarloon, …)`) — it directly determines the rate and therefore the withholding, and the entire stated purpose of AD-21 is determinism. Leaving the selector's composition open means two compliant implementors can land in different bands and withhold different tax for the same employee.

Concretely, the jaarloon-basis clause (lines 343–347) says Cases A/B "read prior-year YTD," but YTD in this module is `hr.wage.component.ytd` keyed per **(employee, rule, year)** (AD-9). "Read prior-year YTD" never says **which rule's YTD, or which sum of rules**, composes jaarloon — gross taxable wage? `TOTAL_LOON`? does it include the prior year's bijzondere beloningen themselves, `NONTAXED` (which AD-2 puts outside NET), the verwervingskosten forfeit? Each choice shifts the band.

**Fix direction:** bind jaarloon to a single definition at the spine level (cite the Handleiding's loon-for-the-table definition) and name which YTD rule(s) compose it, even if the field-level detail stays seed. Without this, AD-21's determinism guarantee is undermined at the input.

## MEDIUM — `lookup_marginal_rate` band-edge inclusivity is undefined

**Units in conflict:** the `bijzondere_beloning` data-seeder / EXTRA_TAX implementor (both via AD-5's read contract).

AD-5 (line 110–115) defines `lookup_marginal_rate(jaarloon, 'bijzondere_beloning', date)` as returning "the **single band rate** containing `jaarloon`" with `income_to = 0` meaning the uncapped top band. It never states whether a band is `[income_from, income_to)` or `(income_from, income_to]` — i.e. which band owns a jaarloon that lands **exactly on a boundary**. Tax-table band edges are round numbers (the published bijzondere-beloningen bands sit on figures like 30 000 / 40 000), and real annual salaries land exactly on them. Two compliant implementors choosing opposite half-open conventions select different bands for a boundary jaarloon → different rate → different withholding, with no tolerance (this is a rate selection, not a 0.02 rounding question).

This is the unambiguous-boundary question the prompt's test 5 asks about, and it is new (not among the excluded findings). It sits squarely in `lookup_marginal_rate`/`bijzondere_beloning` and does not implicate general `compute_tax` semantics.

**Fix direction:** state the inclusivity convention for band bounds once in AD-5's read contract (e.g. `income_from ≤ jaarloon ≤ income_to`, top band `income_to = 0` = unbounded), and require seeded bands to be contiguous and non-overlapping under it.

## LOW — `lookup_marginal_rate`-only rule for `bijzondere_beloning` is documentation-only

AD-5 now explicitly assigns `bijzondere_beloning` to `lookup_marginal_rate` and warns that `compute_tax` "must **not** be used" for it (lines 111–115) — this closes the prior review's CRITICAL on this point at the *prose* level. But the prohibition is **documentation-only**: `compute_tax(income, tax_type, date)` accepts any `tax_type` (line 98–104), the `bijzondere_beloning` bands live in the same `hr.tax.bracket` table as every other type, and the high-level Consistency-Conventions rows still associate "bijzondere beloningen rates as dated `hr.tax.bracket` records" with the general "read via `compute_tax()`" pattern. An implementor who skims the convention table rather than the AD-5 read contract can still call `compute_tax('bijzondere_beloning', …)` and get a (wrong) cumulative figure with no error.

**Fix direction:** have `compute_tax` raise if `tax_type == 'bijzondere_beloning'` (an AD-18-style fail-loud guard), making the prohibition enforced rather than advisory.

## LOW — EXTRA_TAX's non-annualisation is correct but only implicit

AD-21 implies EXTRA_TAX does **not** apply AD-4's × 12 / ÷ 12: the band is selected by *jaarloon* (already annual) and the rate is applied to the beloning amount as a one-time figure. This is correct, and AD-4's scoping sentence (line 85, "AD-4 applies only to SVB premium ceilings and thresholds") already excludes a *tax* like `bijzondere_beloning` — so a careful reader will not wrongly annualise. The only residue is a mild tension between AD-4's **Binds** line ("every rule applying a … bracket") and that scoping sentence, for the one bracket (`bijzondere_beloning`) that is neither the lb-tabel nor an SVB premium. Not a live divergence; a one-line clarity nit.

**Fix direction:** add `bijzondere_beloning` / EXTRA_TAX to AD-4's exception note alongside the loonbelasting carve-out, stating jaarloon is used directly and the beloning amount is taxed un-annualised.
