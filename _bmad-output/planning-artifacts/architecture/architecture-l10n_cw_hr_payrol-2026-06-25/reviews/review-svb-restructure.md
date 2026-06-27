# Adversarial review — seams across the SVB/loonbelasting restructure (AD-5, AD-20, AD-21, AD-22)

**Review pass:** 2026-06-27 — VALIDATE (report only; spine not modified)

**Method:** attack the seams *between* the four restructured ADs. Each finding is a pair of units that each obey every AD to the letter yet build incompatibly or compute a wrong statutory amount. Findings that drove the restructure (prior-pass: bijzondere marginal-rate, surcharge excess-band, above-ceiling rate data home, EXTRA_TAX base, and the H-2 cross-`tax_type` ceiling drift) are **not** re-litigated; the H-2 closure is confirmed below.

**Verdict:** FAIL / blocking. The restructure correctly closes the prior holes, but it opens new seams at the joins — most acutely where AD-21 splits one earning across two bases (premium-in, tax-out) through an undefined "category marker," and where AD-22's per-year record stores the *same* statutory quantity in two redundant forms (split AOV/AWW fields; a loongrens given both monthly and annual). The single-record move kills cross-record drift but reintroduces it *intra-record*.

## Findings

### CRITICAL — "bijzondere-beloning category marker" is undefined; the two natural readings diverge on both premium and tax

**Units in conflict:** TAX_INC (Seq 80) implementor / BVZ_PREM_INC (Seq 20) + AOV_PREM_INC (Seq 50) implementor / the bijzondere earning's `category_id` seeder.

AD-21 requires one earning to land on *opposite sides* of two bases simultaneously: bijzondere beloningen **stay in `ALW`** so AD-14's `BASIC + ALW` premium base **includes** them, but are **excluded from the `TAX_INC` base** so they never hit the maandtabel. AD-21 names `TAX_INC` (Seq 80) as "the named owner of that exclusion, via a bijzondere-beloning **category marker**." The term *category marker* is never defined, and the two natural readings are each AD-compliant yet produce different `TAX_INC` **and** different premium:

- **Read as its own category** (the word "category" invites it; AD-2 already carves `NONTAXED` out as a separate category). Then `categories.ALW` no longer contains the bijzondere amount → AD-14's `BASIC + ALW` premium base **excludes** it → premiums under-charge the bonus, directly violating AD-21's "SVB premiums apply to bijzondere beloningen." `TAX_INC` is correct in this reading; the premium is wrong.
- **Read as a flag on an in-`ALW` line.** Then the premium base is correct, but `TAX_INC` must subtract a *subset* of `categories.ALW`. A category total cannot be selectively reduced; the rule needs either a dedicated bijzondere subtotal rule or a `rules.X` reference — a construct the spine never specifies. If that subtotal/marker rule is sequenced **after** Seq 80 it is unreadable by `TAX_INC` (AD-3), so the placement constraint is load-bearing and unstated. `TAX_INC` and the premium are both correct *only if* this unnamed subtotal exists at the right sequence.

Two teams building TAX_INC and the premium bases independently, each obeying AD-2/AD-3/AD-14/AD-21, will pick different readings and ship a payslip where either the premium or the loonbelasting on every bonus is wrong, with NET (AD-2) silently absorbing the difference. Note also the *double-route* risk this guards: AD-21's "no amount taxed by both" depends entirely on this one exclusion being implemented identically by both the TAX_INC author and whoever assigns the earning's category.

**To resolve (advisory):** define the marker concretely — almost certainly "a per-line boolean on the in-`ALW` wage line" plus a named bijzondere subtotal rule (e.g. `BIJZ_BASE`) sequenced **before** Seq 80, with `TAX_INC = categories.BASIC + categories.ALW − rules.BIJZ_BASE.amount`. State that bijzondere is **not** its own category, so AD-14's base keeps it.

### HIGH — AOV/AWW is one combined rule but four split fields; the combine contract is unspecified

**Units in conflict:** AOV_AWW_EMP / AOV_AWW_ER rule implementor / `hr.svb.parameters` data seeder.

AD-22 binds a single employee AOV/AWW rule and a single employer rule, and AD-5 states the employee share as a **combined flat 6.5 %**. But AD-22's fields are **split**: `aov_emp`/`aww_emp` and `aov_er`/`aww_er`. Nothing says whether the combined rule reads one field or the sum:

- Seeder A folds the law into one field: `aov_emp = 6.5, aww_emp = 0`.
- Seeder B is faithful to the statutory split: `aov_emp = 6.0, aww_emp = 0.5`.
- Rule author X reads `aov_emp` only → 6.5 % with A (correct), **6.0 % with B (under-withholds AWW, a plausible-looking wrong number that survives a casual eyeball)**.
- Rule author Y reads `aov_emp + aww_emp` → 6.5 % with B (correct), 6.5 % with A (correct), but would double if A had also populated `aww_emp`.

This is the H-2 drift pattern reborn *inside* the single record: the same statutory quantity (the combined 6.5 %/9.5 %) is representable two ways in one record, so two compliant builds disagree. The employer side (9.5 % across `aov_er`/`aww_er`) has the identical ambiguity.

**To resolve (advisory):** either collapse to single combined fields (`aov_aww_emp`, `aov_aww_er`) matching the single rules, or state explicitly "the AOV_AWW rule reads `aov_emp + aww_emp`" and require seeders to split per the SVB table.

### HIGH — AD-22 selection key drops AD-20's `year`/`valid_from ≤ date` guard → silent stale (or future) rates at the year boundary

**Units in conflict:** two independent `hr.svb.parameters` selection implementors at a January payslip.

AD-20 specifies a *full* WHERE: `active=True`, `period_type` matches, **`year = date.year`**, **`valid_from ≤ date`**, `valid_to` null or `≥ date`, then `order by valid_from desc, id desc limit 1`. AD-22 only says "the record whose **period/year covers** `payslip.date_to`, among `active=True`, ordered `valid_from desc, id desc`" and points at "the AD-20 pattern." It restates the *ordering* but **not the filter**, and the model carries *both* a `year` Integer and `valid_from`/`valid_to` — so "period/year covers" is genuinely ambiguous about which is authoritative.

For a January 2026 payslip (`date_to = 2026-01-31`) when the 2026 SVB record has not yet been uploaded:

- **Implementor A** mirrors AD-20 literally: `year = 2026` filter → no record → **`UserError`** (AD-18 fail-loud, the intended behaviour).
- **Implementor B** reads AD-22 literally: no `year` equality, just `valid_from ≤ date` ordered desc → the **2025** record (`valid_from 2025-01-01 ≤ 2026-01-31`) is selected and **silently applies last year's premiums and ceilings** to a 2026 payslip.

Symmetrically, without an explicit `valid_from ≤ date` upper bound, a 2027 record uploaded early can be selected for a December 2026 payslip. Either way two AD-compliant builds select different records at the boundary, and Implementor B defeats AD-18.

**To resolve (advisory):** restate AD-20's exact filter in AD-22 (`year = date.year` **and** `valid_from ≤ payslip.date_to` **and** `valid_to` null-or-≥), and say which of `year` vs the date range is authoritative when they disagree.

### HIGH — `zv_ov_loongrens` carries two values (monthly *and* annual), and AD-4 annualisation for ZV/OV is unpinned → ~12× divergence

**Units in conflict:** `hr.svb.parameters` seeder / ZV (and OV) rule implementor.

AD-22 lists `zv_ov_loongrens` as **"7 146.10/month, 85 753.20/year"** — one field, two figures — while every other ceiling in the record is annual (100k / 150k / 606 247.08). AD-22's closing rule says **every** SVB rule "caps the **annualised** base at the relevant ceiling field … de-annualises (AD-4)." Compounding it, a ZV/OV loongrens is conceptually a *monthly eligibility cap*, which invites an AD-4 *exception* reading:

- Seeder stores `7146.10`; rule annualises base ×12 and caps at 7 146.10 → premium ≈ 1/12 of correct against an annualised base, or absurd against a monthly one.
- Seeder stores `85753.20`; rule annualises and caps → correct.
- Or the implementor treats ZV/OV as an AD-4 exception (compare *monthly* wage to 7 146.10 directly, no ×12/÷12) — contradicting AD-22's blanket "annualise every SVB rule."

Two compliant builds land ~12× apart. This is the cleanest "obeys both ADs, diverges" pair in the restructure, and like the AOV/AWW split it is intra-record redundancy reintroducing H-2-style drift.

**To resolve (advisory):** store one canonical figure (state annual, value the annual figure), and state explicitly whether ZV and OV annualise (AD-4) or are AD-4 exceptions compared monthly — mirroring how AD-20 spelled out the loonbelasting exception.

### HIGH — `compute_tax`'s surviving basiskorting scalar has no valid v1.0R consumer: orphan, or double-count if AD-13 is wired literally

**Units in conflict:** TAX_INC / EXTRA_TAX implementor / `hr.tax.bracket` basiskorting seeder.

AD-5 narrows `compute_tax` to "the one surviving caller," reading the dated scalars — basiskorting (2 915/yr), verwervingskosten, toeslagen. But **AD-21 states basiskorting "is already applied via the maandtabel"** (that is exactly why EXTRA_TAX uses the *exclusief-basiskorting* table). If the lb-maandtabel already embeds basiskorting, then in the monthly pipeline **nothing legitimately reads the standalone basiskorting scalar** — its `compute_tax` role is orphaned. Yet **AD-13 keeps it as a scalar that "applies automatically to all employees,"** so an implementor wiring AD-13 literally (subtract/credit basiskorting via `compute_tax`) **double-applies** it on top of the maandtabel. Two compliant builds — one trusting AD-21 (table-embedded), one trusting AD-13 (apply the scalar) — produce different loonbelasting for every employee.

This is a direct AD-13 ↔ AD-21 ↔ AD-5 contradiction the restructure surfaced by demoting `compute_tax` to a scalar reader without saying which scalars actually have a runtime consumer in v1.0R.

**To resolve (advisory):** state explicitly that the maandtabel embeds basiskorting, so the basiskorting scalar is **not** applied in the monthly withholding pipeline (retained for IB/other use only) — or, if it is applied, say where and confirm the table is gross. AD-13's "apply automatically" needs reconciling with AD-21's "already applied via the maandtabel."

### MEDIUM — Rate unit (percent `9.5` vs fraction `0.095`) is never pinned for `hr.svb.parameters`

**Units in conflict:** SVB seeder / SVB rule implementor.

AD-22 lists rates as bare prose percents ("9.5 %"), while AD-20's only worked rate example uses a **fraction** (`× 0.465`) and AD-5 gives no global unit convention. A seeder entering `9.5` with a rule multiplying `base × rate` (expecting `0.095`) yields a 100× error. Severity is MEDIUM only because such an error cannot survive the first reconciliation (acceptance tolerance is XCG 0.02) — it is a spec gap that wastes a build cycle, not a production defect. The combined/split AOV-AWW finding above is the more dangerous sibling because it yields a *plausible* wrong number.

**To resolve (advisory):** one sentence in AD-5/AD-22 pinning all stored statutory rates as fractions (matching AD-20's `0.465`).

### MEDIUM — Where verwervingskosten is applied (income reduction vs table-embedded) is unspecified

**Units in conflict:** TAX_INC implementor / verwervingskosten seeder.

AD-13 applies the verwervingskosten forfait (41.67/mo) to all employees and AD-5 stores it as a `compute_tax` scalar, but the spine never says *how* it enters the calculation: as a reduction of taxable income **before** the maandtabel lookup (Seq 80), or whether the published lb-maandtabel already nets the standard forfait (as it does basiskorting, per AD-21). Unlike the basiskorting case I cannot prove a double-count from the spine alone — whether the Curaçao lb-tabel nets the forfait is a mechanics fact not stated here — so this is an **underspecification**, not a proven defect. Two implementors can still diverge: one subtracts 41.67 at TAX_INC, the other relies on the table.

**To resolve (advisory):** state where verwervingskosten is applied and whether the maandtabel is gross or net of it (same fix vehicle as the basiskorting finding).

### MEDIUM — The `[OPEN]` cumulative-YTD premium method reworks the monthly never-gate bases; "does not block" understates it

**Units in conflict:** the future premium-on-bijzondere implementor / BVZ_PREM_INC + AOV_PREM_INC (never-gate, Seq 20/50) / herberekening + idempotent-close.

AD-21's `[OPEN]` item correctly identifies that AD-4's per-month ×12 annualisation mis-fires at the ceiling for a once-yearly lump and that cumulative-YTD is the right method. It is **contained for sub-ceiling payslips** — including the bonus month, the monthly base correctly includes the lump and ×12/÷12 is a no-op, so normal monthly payslips are *not* corrupted (this part of the prompt's seam 5 checks out clean; NET identity per AD-2 also holds). But "does not block AD-22 or the category decision" understates the structural reach: cumulative-YTD changes the premium **input** from the per-month never-gate base (`BVZ_PREM_INC`/`AOV_PREM_INC`, AD-6) to a YTD premie-loon, and must interact with herberekening (AD-9 allows recompute pre-close) and idempotent close (AD-9 recomputes YTD as a pure function of confirmed slips). Reading *committed prior-month* YTD during computation is permitted (AD-9 forbids only *writing* YTD outside close), so there is no hard contradiction — but the never-gate monthly bases stop being the premium's true input, which the `[OPEN]` note does not acknowledge.

**To resolve (advisory):** when the premium-on-bijzondere story is written, state whether the never-gate bases remain authoritative or the premium reads YTD premie-loon, and confirm consistency under herberekening and reopen→re-close.

### LOW / confirmation — Seam 3 (never-gate × AD-22) is a non-issue, with one stale error-contract note

Per the prompt's request, the negative result is documented explicitly: moving SVB rates into the per-year record does **not** harm the never-gate bases. `BVZ_PREM_INC` (20) and `AOV_PREM_INC` (50) are pure `categories.BASIC + categories.ALW` (AD-14) and read **no** rate/ceiling field — the ceiling is applied later in the gated premium rule — so a missing `hr.svb.parameters` record cannot break them. The AD-18 `UserError` fires only when an **enabled** premium reads the absent record; a disabled premium (AD-6) returns 0 without reading it. Consistent.

One minor mismatch: AD-18's error contract says the `UserError` must "name the `tax_type` or `period_type` and date." A per-year `hr.svb.parameters` record is keyed by neither a `tax_type` nor a `period_type` — so AD-18's message contract is stale for the AD-22 model. Recommend AD-18 also cover "the missing per-year SVB parameter record for year N."

## Confirmations requested by the prompt

- **H-2 (shared ceiling drift across `tax_type` records) — CLOSED for its original form.** AD-22 stores each SVB ceiling **exactly once** in one per-year record, so the cross-record drift (one copy updated, a sibling not) is structurally impossible. **Caveat:** drift is reintroduced *inside* the record by redundant fields — the split `aov_emp`+`aww_emp` / `aov_er`+`aww_er` (HIGH above) and the dual monthly+annual `zv_ov_loongrens` (HIGH above). Each redundant representation is a fresh place for two values of one quantity to disagree. H-2's *mechanism* is closed; its *failure mode* (one statutory quantity, two representations) survives at finer grain.
- **`compute_tax` orphan check.** AD-12 and AD-17 are consistent with the narrowed scalar-reader role (AD-12 now attributes "raw loonbelasting" to `lookup_loonbelasting`, not `compute_tax`; both still `round(x,2)` and take an explicit `payslip.date_to`). The remaining inconsistency is **content, not narration**: the surviving basiskorting scalar has no valid v1.0R consumer (HIGH above), so `compute_tax` is correctly *described* but partly *orphaned in use*.

## Severity summary

| # | Severity | Seam | ADs |
| --- | --- | --- | --- |
| 1 | CRITICAL | "category marker" undefined → bijzondere on wrong side of premium/tax base | AD-21 × AD-14 × AD-2 × AD-3 |
| 2 | HIGH | AOV/AWW one rule, split `aov_/aww_` fields, no combine contract | AD-22 × AD-5 |
| 3 | HIGH | AD-22 selection drops AD-20's `year`/`valid_from≤date` guard → stale/future record | AD-22 × AD-20 × AD-17 × AD-18 |
| 4 | HIGH | `zv_ov_loongrens` monthly+annual dual value; ZV/OV annualisation unpinned | AD-22 × AD-4 |
| 5 | HIGH | basiskorting scalar orphan / double-count vs maandtabel | AD-5 × AD-13 × AD-21 |
| 6 | MEDIUM | rate unit (percent vs fraction) never pinned | AD-22 × AD-5 × AD-20 |
| 7 | MEDIUM | verwervingskosten application point unspecified | AD-13 × AD-5 × AD-20 |
| 8 | MEDIUM | `[OPEN]` cumulative-YTD reworks never-gate bases / herberekening | AD-21 × AD-6 × AD-9 × AD-4 |
| 9 | LOW | Seam 3 non-issue confirmed; AD-18 error contract stale for per-year record | AD-22 × AD-6 × AD-18 |
