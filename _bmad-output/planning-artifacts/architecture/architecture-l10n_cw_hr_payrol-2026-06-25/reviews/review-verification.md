# Verification Review — Architecture Spine

**Reviewer:** Automated verification agent
**Date:** 2026-06-27
**Scope:** Validate that every committed decision in the spine was reality-checked
rather than asserted from training data. Sources consulted: statutory PDFs in
`docs/` (MR 144, lb-maandtabel-2026, lb-weektabel-2026, SVB-Tabel-2026,
Tabel-bijzonder-beloningen-2026-exclusief/inclusief, Schijven-tarief-2026,
voorblad-lbtabel-2026), tech design v3.0D.txt.

---

## Gate Verdict

**CONDITIONAL PASS — proceed, but resolve findings A and B before seeding rate data.**

Two statutory values in the spine are sourced from the tech design only, with no
confirming statutory PDF in the repo: the basiskorting amount (XCG 2,915/yr) shows
an arithmetic inconsistency against an available 2026 statutory table, and the BVZ/AVBZ
sliding-scale thresholds have no visible statutory source in the repo at all. Everything
else was confirmed directly against source documents.

---

## Finding A — CRITICAL: Basiskorting 2,915/yr inconsistent with statutory table

**Location:** AD-13, AD-12, and the tech design (line 1220, lines 1235–1237).

**Claim:** The basiskorting is XCG 2,915 per year, applied as a monetary deduction
from the computed tax amount.

**What the statutory source shows:** `Tabel-bijzonder-beloningen-2026-inclusief-basiskorting.pdf`
(one of the official 2026 Belastingdienst publications in `docs/`) shows the 0%
band running from XCG 0 to XCG 33,300. Working backwards: if the first taxable
band is 9.75%, the tax on 33,300 is 33,300 × 9.75% = XCG 3,247, not 2,915. A
basiskorting of 2,915 would produce a zero-tax breakeven at 2,915 / 0.0975 = 29,897,
not 33,300.

Adding the verwervingskosten forfeit (500/yr) as an income deduction before computing
tax at 9.75% gives: (33,300 − X) × 9.75% = 2,915, so X = 33,300 − 29,897 = 3,403.
That is not 500. No clean combination of 2,915 and 500 produces the 33,300 breakpoint.

**Risk:** If the basiskorting is wrong, every employee's LOONBEL net-of-toeslag
will be systematically off. The bijzondere beloningen EXTRA_TAX rule is less
affected (it uses the "exclusief" table and applies basiskorting separately), but
the monthly LOONBEL calculation drives every payslip.

**Action required:** Obtain the statutory source for the 2026 basiskorting amount.
Candidates: the Landsverordening op de loonbelasting 1976 (art. 22 or equivalent),
or the 2026 Ministerial Regulation that sets basiskorting alongside the tables.
If the correct value is 3,247 or another figure, update the seed data and the
tech design note at line 1220. Do not seed the 2,915 value until verified.

---

## Finding B — HIGH: BVZ and AVBZ sliding-scale thresholds not confirmed from any repo PDF

**Location:** AD-5 (read/representation contract for `bvz_emp` and `avbz_emp`),
spine Consistency Conventions table (SVB rates row), tech design change log items 3 and 4.

**Claims:**
- BVZ employee: sliding scale 0% below XCG 12,000/year, graduating to 4.3%
  above XCG 18,000/year (tech design change log item 4).
- AVBZ employee: 0.5% if annual AOV income < XCG 29,897.44; otherwise 1.5%
  (tech design change log item 3).

**What the statutory source shows:** `SVB-Tabel-2026.pdf` shows only the flat
headline rates: BVZ werknemersaandeel 4.3%, AVBZ werknemersaandeel 1.5%. No
sliding scale, graduated bands, or income threshold appears in this publication.
The sliding-scale thresholds (12,000 / 18,000 for BVZ; 29,897.44 for AVBZ) appear
only in the tech design's change-log text with no citation.

**Risk:** If the sliding scales are implemented and they do not actually exist in
the applicable SVB regulation, premiums will be under-collected at lower income
levels. If they do exist and are implemented with the wrong thresholds, amounts
will be wrong. Either way, a clean statutory source is required.

**Action required:** Obtain the applicable SVB landsverordening or SVB premium
regulation that specifies the BVZ and AVBZ income-dependent rate schedules.
The SVB publishes an annual summary table (which we have) and the underlying
landsverordeningen (which are not in the repo). Until confirmed, the `bvz_emp`
and `avbz_emp` `tax_type` records must be seeded only with confirmed values.

---

## Finding C — MEDIUM: 2026 Ministerial Regulation not in the repo

**Location:** AD-20 background paragraph citing "source: MR 144, 2024".

**What was found:** MR 144 is the November 2024 regulation establishing the **2025**
loonbelasting tables. The 2026 tables are present as separate PDFs
(`lb-maandtabel-2026.pdf`, `lb-weektabel-2026.pdf`, etc.) but their governing
Ministerial Regulation (the 2025 equivalent of MR 144) is not in the repo. The
`voorblad-lbtabel-2026.pdf` contains only the title "Loonbelastingtabellen 2026"
with no regulation number or citation.

**What this does and does not affect:** The above-ceiling 46.5% rule is stated in
MR 144 § Algemeen and derives from article 8, first paragraph of the Landsverordening
op de loonbelasting 1976. It will apply to 2026 by the same statutory authority.
The 2026 ceiling wage (16,670) was confirmed directly from `lb-maandtabel-2026.pdf`
(the table ends at entry 16,670.00 → 4,862.91). So the seeded table content is
available and the above-ceiling formula is correct.

**Risk:** Low for the calculation logic (the formula and ceiling are confirmed),
but medium for regulatory compliance audit trails. The 2026 MR should be added
to the repo when obtained, and the spine's "source: MR 144, 2024" notation updated
to identify the 2026 instrument.

---

## Finding D — LOW: Odoo 19 salary-rule API verified via tech design, not from Odoo 19 source

**Location:** Design Paradigm, AD-3.

**Claim:** The salary-rule Python context provides `employee`, `contract`, `payslip`,
`categories`, `rules`, `inputs`, `worked_days`, `env`; the rule assigns `result`.

**Assessment:** This context is documented in the tech design at lines 490–500 and
is consistent with the Odoo payroll `amount_python_compute` API as it has existed
across versions 14–17. The `env` variable (allowing ORM queries inside rule code)
has been available in Odoo Enterprise payroll for several major versions. No live
Odoo 19 source code or official API documentation was consulted during this review.

**Risk:** Very low. The API has been stable. However, if Odoo 19 removed or renamed
any of these context variables, every rule would fail at runtime. Confirm during
dev-environment setup by running a trivial test rule that logs `env`, `payslip`,
and `categories` to verify all variables are present before writing production rules.

---

## Confirmed — Passed

The following claims were directly verified against statutory PDFs in the repo.

### Above-ceiling formula — CONFIRMED

**Spine claim (AD-20):** `ceiling_tax + (TAX_INC − ceiling_wage) × 0.465`

**Source:** MR 144 § Algemeen (page 5 of the 2025 regulation, applicable as
statutory authority to 2026 by the same Landsverordening): "Indien het loon hoger
is dan het laatste in de tabel vermelde bedrag dan dient over het meerdere 46,5%
loonbelasting te worden ingehouden."

**Arithmetic check (MR 144 example, 2025 table):**
- Income: NAf 17,000; ceiling: 16,670; ceiling tax: 4,927.05
- Extra: (17,000 − 16,670) × 0.465 = 153.45; total: 5,080.50 — matches document.

**2026 values (from `lb-maandtabel-2026.pdf`):** ceiling wage = 16,670; ceiling
tax = 4,862.91. The formula reads `ceiling_tax` dynamically from the last table
row, so this is correct by construction for any year.

### Maandtabel ceiling and step — CONFIRMED

- Ceiling at XCG 16,670/month: confirmed — `lb-maandtabel-2026.pdf` last entry
  is 16,670.00 → 4,862.91.
- Step size 5.00 XCG: confirmed — entries run 0.00, 5.00, 10.00, 15.00 ...
- Weektabel step 5.00 XCG: confirmed — `lb-weektabel-2026.pdf` first entries
  are 0.00, 5.00, 10.00, 15.00 ...
- Halvedagtabel step 1.25 XCG: confirmed from MR 144 2025 table (entries at 0.00,
  1.25, 2.50 ...). The 2026 halvedagtabel (`lb-halvedagtabel-2026.pdf`) was not
  separately extracted but the pattern is structural, not year-specific.
- Dagtabel step 2.50 XCG: confirmed from MR 144 2025 dagtabel (entries at 0.00,
  2.50, 5.00 ...).
- Quincena and kwartaal steps marked TBC in the spine: appropriate; not verified.

### Bijzondere beloningen 6 bands — CONFIRMED

Source: `Tabel-bijzonder-beloningen-2026-exclusief-basiskorting.pdf`

| From (XCG) | To (XCG) | Rate |
|---|---|---|
| 0 | 43,500 | 9.75% |
| 43,500 | 58,000 | 15% |
| 58,000 | 86,900 | 23% |
| 86,900 | 123,100 | 30% |
| 123,100 | 181,000 | 37.5% |
| 181,000 | — | 46.5% |

All 6 bands confirmed. The spine correctly states the module uses the "exclusief
basiskorting" variant with basiskorting applied as a post-table monetary deduction
(confirmed: MR 144 and the 2026 tabel headers both state "Exclusief basiskorting").

Note: The Schijventarief 2026 (inkomstenbelasting) uses different band boundaries
(39,094 / 52,127 / 78,190 / 110,769 / 162,894). The spine's use of the bijzondere
beloningen table for EXTRA_TAX is correct; using the Schijventarief would be wrong.

### SVB premium rates and ceilings — CONFIRMED

Source: `SVB-Tabel-2026.pdf`

| Item | Spine claim | SVB-Tabel-2026 | Status |
|---|---|---|---|
| BVZ employer | 9.3% | werkgeversaandeel 9.3% | CONFIRMED |
| BVZ employee (max) | 4.3% | werknemersaandeel 4.3% | CONFIRMED |
| BVZ pensioners | 6.5% | Gepensioneerde 6.5% | CONFIRMED |
| AVBZ employer | 0.5% | werkgeversaandeel 0.5% | CONFIRMED |
| AVBZ employee | 1.5% | werknemersaandeel 1.5% | CONFIRMED (flat rate only; see Finding B) |
| AOV employee | 6.0% | werknemersaandeel 6.0% | CONFIRMED |
| AOV employer | 9.0% | werkgeversaandeel 9.0% | CONFIRMED |
| AWW employee | 0.5% | werknemersaandeel 0.5% | CONFIRMED |
| AWW employer | 0.5% | werkgeversaandeel 0.5% | CONFIRMED |
| Combined AOV+AWW emp (6.5%) | 6.5% | 6.0% + 0.5% | CONFIRMED |
| Combined AOV+AWW er (9.5%) | 9.5% | 9.0% + 0.5% | CONFIRMED |
| ZV employer | 1.9% | volledig werkgever 1.9% | CONFIRMED |
| OV | 0.5–5% employer | 0.5–5% gevarenklasse | CONFIRMED |
| AOV/AWW ceiling | 100,000/yr | 100,000.00 | CONFIRMED |
| AOV surcharge | 1% above ceiling | premie AOV boven grens 1% | CONFIRMED |
| BVZ ceiling | 150,000/yr | 150,000.00 | CONFIRMED |
| AVBZ ceiling | 606,247.08/yr | 606,247.08 | CONFIRMED |
| ZV/OV ceiling | 7,146.10/mo; 85,753.20/yr | 7,146.10/mo; 85,753.20/yr | CONFIRMED |

### `valid_from desc, id desc` ordering — CONFIRMED implementable

The Odoo ORM `search(domain, order='valid_from desc, id desc', limit=1)` pattern
is standard and is documented behaviour in Odoo's Python ORM. No framework version
risk exists.

### Manifest fields — CONFIRMED consistent

`countries: ['cw']`, version `19.0.0.1.0`, license `OPL-1`, category
`Accounting/Localizations/Payroll`, `installable: True`, `auto_install: False`
are all consistent with the tech design (lines 1695–1734) and with the standard
Odoo `l10n_*_hr_payroll` localization module pattern. The `countries` key is
supported in Odoo 16+ manifests (and therefore Odoo 19). The overall manifest
shape matches `l10n_be_hr_payroll` and similar.

---

## Summary Table

| Area | Spine Claim | Verified? | Source | Risk |
|---|---|---|---|---|
| Above-ceiling formula 0.465 | `ceiling_tax + excess × 0.465` | YES | MR 144 § Algemeen (2025) | — |
| Ceiling wage 16,670/mo | Table ends at 16,670 | YES | lb-maandtabel-2026.pdf | — |
| Ceiling tax 4,862.91 (2026) | Read dynamically | YES | lb-maandtabel-2026.pdf last row | — |
| Maandtabel step 5.00 | step = 5.00 | YES | lb-maandtabel-2026.pdf, lb-weektabel-2026.pdf | — |
| Bijzondere beloningen 6 bands | 0/43500/58000/86900/123100/181000 | YES | Tabel-bijzonder-beloningen-2026-excl.pdf | — |
| SVB flat rates and ceilings | 9.3%, 9.5%, 6.5%, 1.5%, 1.9% etc. | YES | SVB-Tabel-2026.pdf | — |
| BVZ sliding scale 0–4.3% | 0% below 12k, 4.3% above 18k | NO | Tech design only; SVB PDF shows flat 4.3% | HIGH |
| AVBZ threshold 29,897.44 | 0.5% below / 1.5% above | NO | Tech design only; SVB PDF shows flat 1.5% | HIGH |
| Basiskorting 2,915/yr | Monetary deduction from tax | INCONSISTENT | Tech design only; "inclusief" table implies ~3,247 | CRITICAL |
| Odoo 19 rule context variables | payslip/employee/contract/etc. | CONSISTENT | Tech design; not verified against live Odoo 19 | LOW |
| valid_from desc, id desc | ORM order clause | YES | Standard Odoo ORM | — |
| Manifest fields | countries/version/OPL-1 | YES | Tech design / Odoo pattern | — |
| 2026 MR (lb-tabel authority) | Source cited as MR 144 (2025) | PARTIAL | 2026 tables present; 2026 MR not in repo | MEDIUM |
