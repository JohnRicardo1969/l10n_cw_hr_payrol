::: {custom-style="Title"}
Adversarial Seam Review — AD-23 / AD-24 / hardened AD-20
:::
::: {custom-style="Subtitle"}
Lei di Bion exempt overtime, cumulative annual-maximum premiums, exclusief maandtabel
:::

# Verdict

**One sentence:** AD-24's cumulative method is specified against a YTD store (`hr.wage.component.ytd`) that is a single annual scalar with no period dimension, so two implementors each obeying the ADs build incompatible premium rules that commit a wrong, non-rounding annual amount whenever a ceiling-crossing period is reopened or an earlier period is herberekend — and four narrower seams (premie-loon base definition, AD-6 disable clawback, Lei di Bion weekly cap, exclusief guard) each admit divergent compliant builds.

This review **validates only** — the spine was not modified.

# Method

Each finding constructs a pair of units (A, B) that **both** satisfy the cited ADs yet build incompatibly or compute different amounts. Severity reflects whether the divergence commits a wrong **posted** amount beyond the XCG 0.02 tolerance (Critical/High) or is contained/cosmetic (Medium/Low). Worked numbers use the stated 2026 rates: AOV/AWW emp 6.5 %, BVZ emp 4.3 %, ceilings AOV/AWW 100 000, BVZ 150 000, AVBZ 606 247.08.

# Findings

## CRITICAL-1 — AD-24 "as of prior closed period" is unrepresentable in AD-9's scalar YTD; reopen / herberekening commits a wrong annual premium

**Seams attacked:** AD-24 cumulative ↔ AD-9 YTD ↔ AD-21 freeze/herberekening (tasks 1 + 2, unified).

**Root cause.** AD-24 requires each premium rule to read premie-loon and premium-withheld **"as of the prior closed period"** (line ~527). AD-9 stores `hr.wage.component.ytd` as **one annual scalar per (employee, rule, year)**, recomputed at close as the *sum over that year's confirmed payslip lines* (lines 168–172). A single annual scalar **has no period axis** — "as of the prior period" is recoverable from it *only* while runs are processed in strict forward order, where the open period is simply not yet in the scalar. The instant a period is reopened or an earlier period is herberekend, the scalar can no longer express "before this period," and AD-24's self-correction claim ("herberekening recomputes forward … self-corrects by construction," line 531-533) is **falsified by its own commit model**.

**Two compliant, incompatible implementations.**
- **Impl A** reads the stored `ytd` scalar (`ytd_amount` for the premie-loon base and for the premium) and treats it as "prior period." Obeys AD-24 ("read the year's `hr.wage.component.ytd`") and AD-9.
- **Impl B** ignores the scalar and **sums the year's confirmed payslip lines excluding the current run** live during compute. Also obeys AD-24 ("read the year's YTD") and AD-9 (reads, does not write).

A and B agree on a clean forward year and disagree on every reopen/herberekening — exactly the scenario AD-24 claims to handle.

**Concrete wrong number (reopen a ceiling-crossing period).** Ceiling C = 100, rate r = 0.065 (figures scaled for clarity).
- Periods 1–4: premie-loon 20 each → YTD loon 80, YTD premium 5.20.
- Period 5 first pass, base 40: `min(80+40, 100)=100`; `premium_to_date = 6.50`; `6.50 − 5.20 = 1.30` withheld (only the 20 of headroom is charged). Close sets scalars: YTD loon = 120, YTD premium = 6.50.
- **Reopen period 5, recompute (base unchanged).** Impl A reads the stored scalar (loon 120 — already includes period 5) and adds the period base → capped at 100 → `premium_to_date = 6.50`; `already_withheld` scalar = 6.50 → **period-5 premium = 0.00**. The 1.30 has vanished.
- Re-close recomputes YTD premium = Σ confirmed lines = 5.20 + 0.00 = **5.20** — the year is now **1.30 short**.

This heals only if a *later* period is also recomputed and reclaims the headroom. **If the crossing period is December** (or the last paid period of the year), there is no later period: the annual premium is committed **1.30 light** — orders of magnitude beyond XCG 0.02, and **not** a rounding artifact. Impl B (live sum excluding the current run) computes the correct 1.30 on reopen.

**Seam 2 is worse than the cumulative claim admits — the scalar reads *future* data.** AD-9's scalar = sum of **all** still-confirmed periods 1–12. After period 3 is reopened and re-closed, recomputing period 4 against the scalar reads a value contaminated by periods 5–12, not "as of period 3." "Recompute forward" is therefore both (a) **unenforced** — nothing reopens the already-closed, possibly already-distributed (AD-16) later runs, so a run can close leaving stale later periods — and (b) **unsound against a scalar store** even if performed, unless every later period is reopened simultaneously and recomputed in strict ascending order. The spine specifies **no recompute ordering and no forward-propagation trigger**.

**What the spine must pin (not fixed here):** premie-loon and premium-withheld used by the cumulative cap must be obtained as a **period-bounded** quantity — "Σ confirmed lines with `date_to < this payslip.date_to`," not the annual scalar — and herberekening must mandate ascending forward recompute of every later confirmed period. As written, AD-24's robustness property is unattainable on AD-9's data model.

## HIGH-2 — premie-loon YTD base is undefined; the two natural derivations diverge above the ceiling and across Lei di Bion exemption

**Seams attacked:** AD-24 ↔ AD-6 never-gate storage (task 1), AD-23 ↔ AD-24 ↔ AD-14 (task 3). These are one question: *which stored quantity is "premie-loon YTD"?*

The cumulative formula needs the YTD **base** (premie-loon), but AD-24 never says which rule's YTD row holds it, and AD-9 never says hidden intermediates accumulate YTD. Candidates, all defensible:
- **(a)** the never-gate base `BVZ_PREM_INC`(20) / `AOV_PREM_INC`(50) own YTD rows — these are `categories.BASIC + categories.ALW` **minus** flagged Lei di Bion-exempt components (AD-23) and **including** bijzondere beloningen (AD-21): the **correct** premie-loon.
- **(b)** the raw AD-14 base `categories.BASIC + categories.ALW` recomputed at YTD time — this **includes** Lei di Bion-exempt overtime (it stays in `ALW`/`NET`, AD-23), so it **overstates** premie-loon by every exempt hour, overcharging premium and reaching the ceiling early. This is precisely the "exclusion applied in the period calc but not in YTD → drift" failure task 3 names.
- **(c)** re-derive premie-loon = `premium_YTD ÷ rate`. **Fails above the ceiling**: once capped, premium is pinned at `ceiling × r`, so `÷ r` yields the *ceiling*, not the accumulated base — the next period then sees no headroom consumed and under/over-charges. Concretely an employee at YTD loon 700 000 (AVBZ ceiling 606 247.08): premium_YTD = 606 247.08 × r; `÷ r` = 606 247.08, losing the 93 752.92 of over-ceiling base, so a later negative adjustment or a base correction computes against the wrong cumulative.

Impl using (a), (b), or (c) all "read the year's YTD" per AD-24; they commit different premiums. **The spine must state: premie-loon YTD = the net Seq 20 / Seq 50 base rule's own `ytd` row (option a), stored independently of the premium row, and hidden intermediates DO accumulate YTD.** Until then, HIGH-2 also re-exposes CRITICAL-1: if hidden intermediates are decided to *not* get YTD rows (a reasonable "YTD is reporting-only" reading), there is **no** stored premie-loon at all and the cumulative method cannot be implemented as written.

## HIGH-3 — AD-6/AD-7 disable interacts with AD-24 to claw back premium on re-enable

**Seam attacked:** AD-24 ↔ AD-6 never-gate / AD-7 active-vs-enabled (task 1).

The never-gate base (`BVZ_PREM_INC`, `AOV_PREM_INC`) **always executes** (AD-6), so premie-loon YTD keeps accruing while a premium rule is gated `enabled=False`. The premium rule itself is **not** in the never-gate set, so during the disabled months it returns 0 and accumulates **no** premium-withheld YTD. The cumulative formula then claws the whole gap back on re-enable:

- BVZ emp 4.3 %, base 1 000/mo, below ceiling. Periods 1–3 enabled → withheld 43.00 ×3 = 129.00 (YTD premium 129.00, YTD loon 3 000). Periods 4–6 `enabled=False` → premium 0, **but never-gate base still accrues** → YTD loon = 6 000, YTD premium still 129.00. Period 7 re-enabled: `premium_to_date = min(7 000, 150 000) × 0.043 = 301.00`; `301.00 − 129.00 =` **172.00** withheld in one month — i.e. the three "exempt" months 4–6 are **retroactively clawed back**.

This violates the AD-6 expectation that a disabled premium "downstream receives 0.00, never a stale value" and the AD-7 audit use ("statutory exemption = `active=True, enabled=False`"): under AD-24 a mid-year exemption does not yield clean zeros — it merely **defers** the premium to the re-enable period. Two compliant implementors differ on whether a disable should also **remove its base from cumulative premie-loon** (it cannot, because the base rule is never-gated and knows nothing about the premium's gate). The spine must resolve the statutory question — does an `enabled=False` premium month also exempt that month's wage from the annual cumulative base, or only defer? — because the two readings produce different annual totals.

## HIGH-4 — AD-23 "≤10 hrs/week" has no monthly conversion and no named approval model; eligibility diverges

**Seam attacked:** AD-23 eligibility ↔ approval (task 4).

- **Weekly cap in a monthly run.** AD-23 caps exemption at "10 overtime hours/week" and taxes the excess (lines 503-509), but v1.0R is **monthly only**. The spine gives **no** week→month conversion. Compliant implementors diverge: Impl A uses 40 (4 weeks), Impl B uses **43.33** (the 52/12 = 4.333 weeks/month implied by the fixed 173.33 hr/month divisor in CLAUDE.md), Impl C counts actual ISO-week boundaries in the period (some months straddle 5). For 50 exempt overtime hours at the worked-example rate, A exempts 40 / B exempts 43.33 / C varies — **different loonbelasting AND different premie-loon** (the exempt portion leaves both bases, AD-23). The worked example ("10 overuren") sidesteps the question entirely. The cap unit must be fixed as a monthly figure in the spine.
- **Shared cap ambiguity.** If an employee has both *regulier* overwerk and Lei di Bion overwerk, does the 10/week cap count only flagged-exempt hours or all overtime hours? Unstated → divergent exempt amounts.
- **Approval is unnamed and its temporal semantics are undefined.** AD-23 says the beschikking must be "approved by the Payroll Manager" and "without that approval recorded, the overtime is not exempt," but **names no field or model** for the recorded approval (a boolean on the employee? a dated beschikking record? a wage-line flag?). With effective date `payslip.date_to` (AD-17), a mid-period revocation flips the **entire** period to taxable retroactively — or not, depending on whether an implementor reads approval as point-in-time at `date_to` or "valid for the whole period." Two compliant builds, two answers, on a statutory exempt/taxable boundary.

## MEDIUM-5 — the exclusief-table guard ("lowest wage rows are non-zero") is a weak discriminator

**Seam attacked:** AD-20 exclusief guard ↔ AD-13 (task 5).

AD-20's load guard verifies the loaded maandtabel is the *exclusief* variant by checking "its lowest wage rows are non-zero" (line 348). This is an **insufficient discriminator** of inclusief vs exclusief. The two variants differ by the **width of the zero-tax band**: the inclusief table shows tax 0.00 up to roughly `basiskorting ÷ marginal_rate`, whereas the exclusief table taxes from the first gulden. A correct guard would compare a **known wage point against the known exclusief value** (or assert the zero-tax band width ≈ 0), not merely test the first row for non-zero. The "non-zero lowest row" heuristic is fragile at both ends: it can **false-reject** a legitimately-published exclusief table if its first one or two rows round to 0.00 at the publication step, and it gives only weak assurance against an inclusief table whose zero-band a careless check might not reach. (Note: I could not render the MR 144 / `lb-maandtabel-2026.pdf` first rows in this environment — `poppler-utils` is absent — so the false-reject branch is argued structurally, not confirmed against the printed rows; the "weak discriminator / use a known wage point" conclusion holds regardless.) Tighten the guard to a value comparison against the known exclusief figure.

## MEDIUM-6 — AVBZ is bound to cumulative but has no named premie-loon base

**Seam attacked:** AD-24 ↔ AD-6 never-gate set (task 1, extension).

AD-24 binds **AVBZ** (employee and employer) to the cumulative method (line 515), but the never-gate set (AD-6) lists only `BVZ_PREM_INC`(20) and `AOV_PREM_INC`(50) — **no AVBZ base rule**. Which premie-loon does AVBZ's cumulative cap read? Reusing `AOV_PREM_INC` may be numerically fine (same `BASIC + ALW`), but it is **unstated**, and it is another instance of HIGH-2's unpinned premie-loon base. If an implementor instead derives AVBZ premie-loon from `AVBZ_EMP_YTD ÷ rate`, it breaks above the 606 247.08 ceiling (HIGH-2c). State explicitly which base row AVBZ's cumulative read uses.

## LOW-7 — "ordinary monthly payslips are unaffected" is technically false (rounding redistribution); the mid-year-raise hypothesis is debunked

**Seam attacked:** AD-24 below-ceiling claim (task 6).

**Verified, with one correction.** Below any annual ceiling the `min()` is inert and the cumulative formula telescopes:

`this_period = round(YTD_loon_incl × r, 2) − round(YTD_loon_before × r, 2)`

This equals the simple `round(base × r, 2)` **only when** `sum(round) = round(sum)`, which is not generally true. Example: base 1 234/mo at BVZ 4.3 % gives a true 53.07 month interleaved among 53.06 months under cumulative, versus a constant 53.06 under flat-rate — a ±0.01 wobble even for a **constant-salary** employee. So AD-24's claim that "ordinary monthly payslips are unaffected" (line 535-536) is **slightly false**: cumulative **redistributes** rounding across months. The effect is ≤ 0.01/period and inside the XCG 0.02 tolerance, hence **Low** — but the spine sentence overclaims and should say "unaffected to within rounding."

**Mid-year-raise hypothesis debunked (verification, not a finding):** a raise that stays **below** the ceiling does **not** break per-period equality — cumulative is linear below the cap, so periods before the raise charge `old_base × r` and periods after charge `new_base × r`, identical to flat-rate (modulo the rounding above). The raise only matters when it pushes YTD **across** the ceiling, which is the legitimate case AD-24 exists for. The hypothetical that a below-ceiling raise breaks equality is false.

# Summary table

| # | Severity | Seam | Two compliant builds diverge on | Wrong posted amount? |
|---|----------|------|----------------------------------|----------------------|
| 1 | Critical | AD-24 ↔ AD-9 ↔ AD-21 | scalar YTD vs live period-bounded sum on reopen/herberekening | Yes — December crossing commits short, ≫ 0.02 |
| 2 | High | AD-24 ↔ AD-6 / AD-23 / AD-14 | which row is premie-loon YTD (net Seq20/50 vs raw BASIC+ALW vs premium÷rate) | Yes — above ceiling & per exempt hour |
| 3 | High | AD-24 ↔ AD-6 / AD-7 | disable = exempt base vs defer premium | Yes — clawback lump on re-enable |
| 4 | High | AD-23 eligibility/approval | weekly cap → monthly (40 vs 43.33 vs ISO); approval field & revocation timing | Yes — exempt amount differs |
| 5 | Medium | AD-20 guard ↔ AD-13 | "first row non-zero" vs known-value comparison | Guard false-reject / weak assurance |
| 6 | Medium | AD-24 ↔ AD-6 set | AVBZ cumulative base unnamed | Potentially, above 606 247.08 |
| 7 | Low | AD-24 below-ceiling claim | rounding redistribution; raise hypothesis | ≤ 0.01/period (in tolerance) |

# Disposition

CRITICAL-1 and HIGH-2 share one root cause — **the cumulative method (AD-24) is specified against a period-less annual scalar (AD-9) and an unpinned premie-loon base** — and should be resolved together: define premie-loon and premium-withheld as period-bounded sums of confirmed lines (`date_to <` current period), name the net Seq 20/Seq 50 base rule as the premie-loon source, mandate ascending forward recompute on herberekening, and decide whether a disabled-premium month exempts or merely defers its base. HIGH-4 needs a monthly cap figure and a named, dated approval model. The rest are localized.
