# Adversarial review — two AD-compliant units that still diverge

**Review pass:** 2026-06-27 (second pass; replaces first-pass review whose three findings were resolved by Gate fixes 1–3)

**Verdict:** FAIL / blocking. Two independently built rules can each obey every AD to the letter yet still produce wrong statutory tax. The root cause in both cases is the same: the AD-5 per-`tax_type` read contract was added to close the generic divergence hole, but the contract is adequate only for "accumulate from zero" tables. It fails silently — and differently — for every non-accumulation lookup in the pipeline.

## CRITICAL — `bijzondere_beloning` read contract calls `compute_tax` but EXTRA_TAX needs marginal-rate selection, not cumulative accumulation

**Units in conflict:** the `bijzondere_beloning` data-seeder / EXTRA_TAX (Seq 110) rule implementor.

AD-5 read contract for `bijzondere_beloning`: "progressive — `compute_tax` accumulates band-by-band and returns the tax (`income_to = 0` = top band uncapped)." This is the correct description of how loonbelasting is computed on the full `TAX_INC` income.

EXTRA_TAX is different. It selects the marginal rate band that contains `annual_total = rules.TOTAL_LOON.amount * 12`, then applies only that band's rate to `extra_earn` (the bijzondere beloning amount itself). The rate is **not** applied progressively over cumulative income.

If the EXTRA_TAX implementor follows the AD-5 read contract literally and calls `compute_tax(annual_total, 'bijzondere_beloning', date)`, they receive the progressive cumulative tax on the full annual income — a completely wrong number. For an employee earning XCG 80 000/year (sitting inside the 23 % band), `compute_tax` would accumulate: 9.75 % × 43 500 + 15 % × 14 500 + 23 % × 22 000 = XCG 11 476.25 on their ordinary income, then the caller would confuse this large cumulative figure with a rate to apply to `extra_earn`. The correct computation is simply `extra_earn × 0.23`. What EXTRA_TAX needs is the single marginal rate (23 %) — not the cumulative tax on all income up to 80 000.

A second implementor, recognising the mismatch, searches for the bracket record whose `income_from ≤ annual_total < income_to`, reads its `rate`, and applies `extra_earn * rate` — correct, but now deviates from the stated read contract.

There is no spine-defined function for "marginal rate at income X" as opposed to "cumulative tax on income X". The bijzondere beloningen table is stored in `hr.tax.bracket` with `tax_type = bijzondere_beloning`, but the access pattern EXTRA_TAX requires cannot be expressed as a `compute_tax` call. The two implementors obey every AD and still build incompatibly, and one of them computes the wrong withholding amount.

**Fix needed:** add a second utility `lookup_marginal_rate(income, tax_type, date)` that returns the `rate` of the band containing `income` without accumulating, and bind EXTRA_TAX to use it. Alternatively, document exactly what the EXTRA_TAX rule must do with the `bijzondere_beloning` records so "read via `compute_tax`" is overridden for this tax_type.

## CRITICAL — `compute_tax` excess-band algorithm produces wrong surcharge for `aov_aww_surcharge`

**Units in conflict:** the `hr.tax.bracket` data-seeder for `aov_aww_surcharge` / AOV_AWW_1PCT (Seq 62) rule implementor.

AD-5 read contract for `aov_aww_surcharge`: "sliding — multiple dated band records; the rule selects the band by the annualised base and applies that band's `rate`." The surcharge is 1 % on annual income **above** XCG 100 000.

A reasonable seeder stores this as a single band: `income_from = 100 000, income_to = 0 (uncapped), rate = 1.0`. An implementor of AOV_AWW_1PCT then calls `compute_tax(annual_aov, 'aov_aww_surcharge', date)` per the AD-5 contract.

Trace the `compute_tax` body against `annual_aov = 120 000`:

```
remaining = 120 000
bracket: lower=100 000, upper=inf
in_band = min(120 000, inf − 100 000) = 120 000
tax = 120 000 × 0.01 = 1 200
```

Result: XCG 1 200 — which is 1 % of the **whole** base, not of the XCG 20 000 excess. The correct result is XCG 200. The error is 6× on the example above.

The `compute_tax` algorithm reduces `remaining` from `income`, not from `income_from`. A band with `income_from > 0` never consumes the amount below `income_from` — it treats the surplus as if it starts from zero. The algorithm works correctly only when bands partition the full range starting at 0. AD-5's "sliding" contract accommodates BVZ_emp and AVBZ_emp (where the full capped base is multiplied by the applicable rate) but not the surcharge (where only the excess above a threshold is taxed).

Two data-seeders can both obey AD-5's "sliding" description and still produce different results depending on whether they seed a two-band 0→100 000 (0 %) + 100 000→∞ (1 %) structure or a single excess band. The first produces the correct answer via `compute_tax`; the second produces 6× the correct answer.

**Fix needed:** either (a) require that every `aov_aww_surcharge` dataset covers the full range from zero (first band 0→100 000, rate 0 %; second band 100 000→∞, rate 1 %) and document this constraint explicitly in AD-5, or (b) require Seq 62 to compute the surcharge directly using `aov_aww_emp.income_to` as the threshold (not via `compute_tax`). Without this, any seeder who stores only the excess band produces systematically wrong withholding.

## HIGH — Shared statutory ceilings/thresholds split across two `tax_type` records with no single owner

**Units in conflict:** AVBZ_EMP (Seq 70) implementor / AVBZ_ER (Seq 71) implementor; similarly AOV_AWW_EMP implementor / AOV_AWW_1PCT implementor.

AD-5's read contract assigns the AVBZ annual ceiling (XCG 606 247.08) to `avbz_er` as `income_to` ("flat with ceiling — one dated record whose `income_to` is the annual ceiling"). For AVBZ_EMP, the contract says "sliding — multiple dated band records." The AVBZ_EMP sliding bands must also cap at 606 247.08 — but the spine does not say whether the AVBZ_EMP top band stores `income_to = 606 247.08` or whether the AVBZ_EMP rule reads the ceiling from `avbz_er.income_to`.

Two compliant implementors:

- **Implementor A** embeds `income_to = 606 247.08` in the `avbz_emp` top band record. When Belastingdienst raises the AVBZ ceiling, a rate-administrator updates the `avbz_er` record (which the read contract names as the ceiling owner) but does not notice the ceiling is also embedded in the `avbz_emp` top band. AVBZ_EMP silently continues to cap at the old amount.
- **Implementor B** stores no `income_to` on the `avbz_emp` top band (`income_to = 0`, uncapped) and has the AVBZ_EMP rule read `avbz_er.income_to` to derive the cap. These records are now coupled across `tax_type` boundaries — the AVBZ_EMP rule depends on `avbz_er` data, which the localization layer must keep consistent but cannot enforce.

The same split exists for the AOV ceiling (100 000): it lives in `aov_aww_emp.income_to` (flat-with-ceiling) but is also the threshold of the `aov_aww_surcharge` sliding scale. AD-5 says it prevents "two rules holding divergent copies of the same rate" — but the read contract reintroduces exactly that risk for shared ceilings.

**Fix needed:** for each shared ceiling, AD-5 must name one record as the single source of truth and specify which rules must read from it. The alternative is to introduce a ceiling field on `hr.tax.bracket` that is shared across `tax_type` values — but this is a larger model change.

## HIGH — Above-ceiling rate `0.465` in AD-20 is a statutory rate with no data home

**Units in conflict:** `lookup_loonbelasting` implementor / rate-administrator who updates rates at year-end without a code deploy.

AD-20 specifies: "if `TAX_INC > max(wage_from)` for the selected table: `loonbelasting = ceiling_tax + (TAX_INC − ceiling_wage) × 0.465`." The `0.465` (46.5 %) is the statutory marginal rate above the table ceiling.

AD-5 states: "No statutory rate, ceiling, or threshold is a literal in rule Python." The 46.5 % is a statutory rate — the same kind of value the spine says must live in data records to enable rate changes without a code deploy.

However, AD-20 simultaneously states that loonbelasting is NOT in `hr.tax.bracket`, and the `hr.loonbelasting.tabel` model definition in AD-20 defines no field for the above-ceiling rate. There is no data home for 0.465 anywhere in the spine.

Two implementors diverge:

- **Implementor A** hardcodes `0.465` in `lookup_loonbelasting` (following AD-20's formula verbatim, violating AD-5's literal ban).
- **Implementor B** infers that the above-ceiling rate must live somewhere in the table's data (e.g., a `above_ceiling_rate` Float field on `hr.loonbelasting.tabel`) because AD-5 forbids the literal — but this field is not defined in the spine, so they introduce it unilaterally.

When the Minister publishes a corrected table with a different top marginal rate, Implementor A requires a code deploy; Implementor B's field is updated via data upload. Both obey every AD as stated and build different data models.

**Fix needed:** either add an `above_ceiling_rate` field to `hr.loonbelasting.tabel` header (and derive the above-ceiling computation from it), or explicitly exempt this literal from AD-5 (carving it as a formula constant that travels with the code, with the acknowledgement that a rate change here requires a code deploy). The current silence guarantees divergence.

## HIGH — EXTRA_TAX marginal-rate base is undefined: `TOTAL_LOON` (no overtime) versus full category sum (with overtime)

**Units in conflict:** EXTRA_TAX (Seq 110) implementor / overtime rule (Seq 11–14) implementor.

EXTRA_TAX determines the marginal rate band using `annual_total = rules.TOTAL_LOON.amount * 12`. `TOTAL_LOON` (Seq 10) includes only `contract.wage + fringe`; it does not include the overtime amounts in `categories.ALW`.

AD-14 mandates `categories.BASIC + categories.ALW` as the premium base for BVZ_PREM_INC and AOV_PREM_INC, but AD-14 explicitly does not bind EXTRA_TAX. An implementor of EXTRA_TAX who follows AD-14's spirit of "use the full income base including overtime" would write `annual_total = (categories.BASIC + categories.ALW) * 12`. An implementor following the tech design listing writes `annual_total = rules.TOTAL_LOON.amount * 12`.

For an employee whose overtime takes them into a higher band, the two implementations produce different marginal rates and different bijzondere beloning withholding amounts. Both implementors obey every stated AD: AD-3 (reference prior rules only — TOTAL_LOON is prior to Seq 110), AD-14 (does not apply to EXTRA_TAX), AD-5 (rate is data, not literal, per bijzondere_beloning bracket records).

**Fix needed:** AD-14 or a new AD must specify the exact income reference for EXTRA_TAX's band determination. If statutory intent is to include overtime in the marginal income (which is the likely correct reading of the Belastingdienst guidance — bijzondere beloningen are taxed at the employee's actual marginal rate on total income), this must be stated explicitly, because the tech design listing contradicts that intent.

## MEDIUM — AD-9 "confirmed payslip lines" is not bound to an Odoo payslip state; interaction with reopened sibling runs undefined

**Units in conflict:** `action_close()` implementor / `hr.wage.component.ytd` query implementor.

AD-9 says `ytd_amount` is set to the "sum over that year's confirmed payslip lines for the (employee, rule)". "Confirmed" is never mapped to an Odoo `hr.payslip.state` value. Odoo payslip states are `draft`, `verify`, `done`, and `cancel`. The close action confirms and locks payslips before computing YTD — but the Odoo method used (confirm all slips → state `done`? or just the run's slips → state `verify`?) is implementation-defined.

The interaction with reopened prior runs in the same year sharpens this: if January was closed (payslips in `done`) then reopened (state rolls back), February is still closed. When computing February's YTD, does the query include January's payslips (still in `done` from the initial close, or back to `verify` after reopen)? AD-9 says reopen "reverses its posted `account.move`" but does not specify what state January's individual payslips are in after reopen. Two implementors:

- **Implementor A** queries `state = 'done'` for YTD. After January reopen, if payslips revert to `verify`, they are excluded from February's YTD computation — under-counted.
- **Implementor B** queries `state in ('done', 'verify')`. January's reopened payslips are included — potentially double-counted when January is eventually re-closed.

**Fix needed:** AD-9 must name the Odoo payslip state that constitutes "confirmed" and specify what reopen does to individual payslip states. A concrete rule such as "reopen sets the run to draft; individual payslip states revert to draft; re-confirmed slips must pass through verify → done before close" would make the YTD predicate unambiguous.

## LOW — AD-6 never-gate wording does not explicitly prohibit an enabled-check in rule code

AD-6 says never-gate rules "always execute regardless of any flag." This is clear intent, but the wording does not forbid a rule implementor from writing an enabled-check that is always short-circuited because the enabled flag is True. If a T3 wage line is created for a never-gate rule (the spine does not prohibit this) and its `enabled` flag is later set to False by an administrator thinking they are temporarily pausing a rule, the rule would return 0 — a silent, hard-to-diagnose calculation error.

**Recommended clarification:** add one sentence to AD-6: "Never-gate rule code must never read the `enabled` flag; if a T3 wage line exists for a never-gate rule, the `enabled` field is ignored and the line must not be presented with an enabled toggle in the UI."
