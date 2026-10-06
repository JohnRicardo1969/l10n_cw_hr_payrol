# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

This is the design/planning repository for **`l10n_cw_hr_payroll`**, an Odoo 19 Enterprise payroll localization module for Curaçao (country code `cw`). **No module code exists yet** — the repo currently holds the specifications the code will be built from. There is no `__manifest__.py`, no Python, and therefore no build/lint/test workflow. When implementation begins, the module is built on top of Odoo's Enterprise `hr_payroll` engine and is intended to run on **Odoo 19 Enterprise / Odoo.sh** (SaaS is explicitly unsupported — custom modules and Python salary rules are required).

### Source-of-truth documents

Read these before designing or implementing anything; they are authoritative and self-consistent except where flagged below.

- `docs/prd/PRD - v3.0D.md` — Product requirements for the v1.0R release (monthly payroll only). Scope, data models, the canonical salary-rule sequence, rate tables, lifecycle, accounting, acceptance criteria, roadmap.
- `docs/tech_design_l10n_cw_hr_payroll_v3.0D.txt` — Full technical design (the PRD's source). Contains field-level model definitions, salary-rule Python listings, and the file tree.
- `_bmad-output/planning-artifacts/architecture/.../.memlog.md` — The distilled **architecture spine**: the binding invariants (ADs) every salary rule and model must obey. This is the highest-signal file for implementation decisions.
- `docs/*.pdf` — Official 2026 Belastingdienst Curaçao (loonbelasting schijventarief, bijzondere beloningen, lookup tables) and SVB (premiums) publications. These are the statutory ground truth; calculations must reconcile to them within XCG 0.02.
- `docs/figure-0{1,2,3}-*.png` — Module dependency architecture, three-tier wage component model, payroll run lifecycle.

`_bmad/` and `.claude/` are gitignored BMad/tooling scaffolding, not project source.

### Spec-sync discipline (MANDATORY)

Any decision made while working on epics, stories, or implementation that changes a requirement, a statutory rule, a model, a dependency, or an architecture invariant MUST be applied to **all living spec documents in the same working session**, never deferred:

- `docs/prd/PRD - v3.0D.md` — the PRD
- `_bmad-output/planning-artifacts/architecture/.../ARCHITECTURE-SPINE.md` (+ its `.memlog.md`) — the architecture spine
- `_bmad-output/planning-artifacts/Odoo Module Design Epics - EN - v1.0D.md` **and** `- NL -` — the epics/stories pair (bilingual lockstep)
- This file (CLAUDE.md), where a stated convention changes

Add a dated supersession note at each edit (e.g. "decided 2026-07-07, superseding …"). **Excluded** (point-in-time records — never retro-edit): `docs/tech_design_l10n_cw_hr_payroll_v3.0D.txt` and historical review artifacts; the spine rules their literals superseded. Precedents: the category decision, the F1–F3 readiness reconciliations, and the `hr_contract`→`hr.version` (D1) ripple were each applied across the full chain in one pass.

## What the module does

Implements the complete Curaçao statutory payroll framework (loonbelasting + SVB premiums: AOV/AWW, AVBZ, BVZ, ZV, OV) entirely inside Odoo, with no external payroll service. The calculation is a fixed sequence of `hr.salary.rule` records (Seq 10–150) mirroring the official Curaçao payroll pseudocode, one rule per step. v1.0R is **monthly payroll only**; other pay periods and many features are deferred (see PRD roadmap). **Cessantia is permanently out of scope** — if ever reinstated, its rule, GL accounts, and the journal balance formula must change together.

## Architecture invariants

These are binding. Most calculation bugs come from violating one of them; the `.memlog.md` is the full list with rationale.

- **Three layers, dependencies point inward toward Localization.** *Localization* (statutory definitions + data: `hr.salary.rule` extension, `CWMONTHLY`/`CWSTAFF` structures, the CW rules, `hr.tax.bracket`, employee toeslag fields, contract OV%) ← *Application* (config/workflow: `hr.wage.component.set`(+line), `hr.employee.wage.line`, `hr.wage.component.ytd`, apply wizard, views/menus/security) ← *Reports* (QWeb PDF + CSV; **read-only, compute nothing**). A report must never recompute a statutory amount.
- **Strict sequence + reference discipline.** Rules evaluate in ascending sequence (10→150). A rule may reference only *prior* results (`rules.CODE.amount`, `categories.X`) — never a later rule.
- **Sign convention.** Deduction/employee-premium rules return **negative** amounts; employer-cost and base rules positive. `NET` sums `BASIC + ALW + DED` directly relying on `DED` being negative. Employer contributions go to category `ER` and are **excluded** from NET. Overtime goes to `ALW`.
- **Ceilings — cumulative, not ×12 (AD-24/AD-20; supersedes the old annualisation rule, 2026-07-08).** SVB premiums with an **annual** ceiling (AOV/AWW, BVZ, AVBZ) are computed **cumulatively**: premium = rate × min(year-to-date premie-loon, annual ceiling) − premium already withheld this year — never ×12→÷12 (which mis-fires when a once-yearly lump lands in one month). The shared premium bases (`*_PREM_INC`) stay **uncapped** (the AOV 1% surcharge needs the excess above the ceiling); each premium rule applies its own ceiling. ZV/OV use the **monthly** cap directly. Loonbelasting reads the period-specific lb-maandtabel directly (AD-20) — no annualisation anywhere.
- **Dated-rate authority — rates are data, never literals.** *All* statutory rates and ceilings (including every SVB premium, sliding-scale bands, the verwervingskosten forfeit, and basiskorting) live in `hr.tax.bracket` as **append-only** dated records (expire via `valid_to`, insert a new `valid_from`; never delete). Read them via `compute_tax()` / dated lookups. **Decided (AD-5):** the v3.0D salary-rule *listings* hardcode premium literals (9.3%, 6.5%, 9.5%, ceilings, 606247.08, 41.67, 2915) — these must be **refactored to data-driven lookups**, because rate changes must not require a code deploy. This requires a **seed change**: expand `hr.tax.bracket.tax_type` to granular per-(insurance, payer) values (`bvz_emp`, `bvz_er`, `avbz_emp`, `avbz_er`, `aov_aww_emp`, `aov_aww_er`, `aov_aww_surcharge`, `zv`, `ov`, `loonbelasting`, `bijzondere_beloning`) with a defined read contract per type (progressive / flat-with-ceiling / sliding).
- **Enable/disable gate + never-gate list.** Each premium/tax rule checks its `hr.employee.wage.line.enabled`; if `False`, set `result = 0.00` and skip its logic (downstream gets `0.00`, never an error/stale value). The **never-gate** rules always execute regardless of flags because they are shared bases/outputs: `BVZ_PREM_INC`(20), `AOV_PREM_INC`(50), `TAX_INC`(80), `LOONBEL_RAW`(90), `NET`(130), `TOTAL_ER_COST`(150).
- **`active` vs `enabled` are independent.** `active=False` hides from UI **and** excludes from calc. `enabled=False` keeps the line **visible for audit** but returns `0.00`. A statutory exemption for audit = `active=True, enabled=False`.
- **Three-tier decoupling.** Applying a Tier-2 `hr.wage.component.set` to employees is a **one-time copy** (via the apply wizard) into independent Tier-3 `hr.employee.wage.line` records. Later edits to the set do **not** propagate. `hr.employee.wage.line.salary_rule_id` is read-only after creation.
- **Single state-commit point.** `hr.payslip.run.action_close()` is the *only* place results are committed: confirm+lock payslips → upsert `hr.wage.component.ytd` (increment per line) → post the `account.move` (draft→posted) → expose run reports. YTD and the journal are mutated nowhere else. Recompute (herberekening) is allowed only **pre-close**.
- **Accounting balance by construction.** Every employer-cost debit has a matching payable credit; total debit == total credit follows from the NET identity (total loon = net + all employee deductions). GL account numbers in the design are **indicative placeholders**, mapped per company at onboarding (v1.1R) — not requirements.
- **Money/rounding.** Currency XCG; `compute_tax` returns `round(x, 2)`; acceptance tolerance is XCG 0.02 (rounding only). `compute_tax` returns **raw** loonbelasting; toeslagen are applied *afterward* as **monetary deductions from the tax amount** (not as taxable-income reductions), floored at 0.

## Resolved decisions and open questions

**Resolved — overtime in the premium base (AD-14).** The v3.0D source was internally contradictory (`BVZ_PREM_INC` excluded overtime; `AOV_PREM_INC` included it). The product owner confirmed (2026-06-26) that overtime **is** included. All premium bases derive from `categories.BASIC + categories.ALW`, and `BVZ_PREM_INC` must be refactored off `rules.TOTAL_LOON.amount` to that base. No longer a blocking question.

No blocking questions remain for v1.0R. The other open questions (OQ-01..OQ-10) are non-blocking — see the PRD; deferred items are tracked in the architecture spine's Deferred section.

## Conventions when code is added

- Manifest: version `19.0.0.1.0`, category `Human Resources/Payroll` (matches all shipped `l10n_*_hr_payroll` modules — keeps the future official-localization track open; supersedes the v3.0D `Accounting/Localizations/Payroll`, decided 2026-07-07), license `OPL-1`, country `cw` (manifest key `countries: ['cw']`), installable, not auto-installed. Direct depends: `hr`, `hr_holidays`, `hr_payroll`, `hr_payroll_account`, `hr_attendance` — **no `hr_contract`**: the module was removed in Odoo 19; contracts are absorbed into core `hr` as the `hr.version` model (extend `hr.version`, not `hr.contract`; decided 2026-07-07, review D1).
- Salary-rule `amount_python_compute` context: `employee`, `version` (the `hr.version` record — Odoo 19 replaces the v3.0D `contract` variable), `payslip`, `worked_days`, `inputs`, `categories`, `rules`, `env` — must assign `result`. Hidden intermediates carry `appears_on_payslip = False`.
- UI strings and model menus are Dutch (e.g. Salarisadministratie → Configuratie → Tarieven); keep statutory terms in their official form (`basiskorting`, not `basisaftrek`).
- Working-hours divisor is the fixed constant **173.33 hrs/month** (8h × 5d × 52wk ÷ 12).
- Official-localization conformance (added 2026-10-06): before every commit, `tools/check_l10n_conformance.py` (git pre-commit hook, warnings only) compares the module with the conventions in `docs/reference/official-localization-checklist.md`. A new divergence is either fixed or recorded in `docs/reference/official-localization-divergences.md` in the same change; deciding an Open divergence is a PO decision and follows the spec-sync discipline.
- Upgrade watch list (added 2026-10-06): every change that hooks into Odoo (an inherited model, an overridden method, a referenced XML id, a relied-on behaviour) adds an entry to `docs/reference/upgrade-watch-list.md` in the same change. Append new entries; never renumber existing ones, because other docs cite them as `§N.M`.

## Markdown output conventions

When generating Markdown deliverables (e.g. `_bmad-output/planning-artifacts/Odoo Module Design Epics - EN - v1.0D.md` and other planning/output docs), follow these rules so they convert cleanly to Word via pandoc:

- **No horizontal-rule separators** (`---`, `***`, `___`) in the document body. *Exception:* a leading YAML frontmatter block delimited by `---` is allowed where a tool requires it (e.g. BMad `stepsCompleted` / `inputDocuments`).
- **Headings: at most 3 levels, and the heading structure starts at Heading 1** (`#` → `##` → `###`; never deeper).
- **Title + subtitle** at the top, as pandoc custom-style fenced divs:

  ```
  ::: {custom-style="Title"}
  The Title Text
  :::
  ::: {custom-style="Subtitle"}
  The Sub-Title Text
  :::
  ```

- **Blank line before the first bullet:** after any heading or label that introduces a bulleted list, leave one empty line before the first `-` item.

## Working principles (Karpathy Skills)

Four general coding principles, each anchored to where it bites hardest in *this* repo.

- **Think Before Coding** — State assumptions explicitly; if uncertain, ask. Present multiple interpretations when they exist rather than proceeding on a silent guess. Here this is not optional: the design has an **open blocking question** (is overtime in the premium base?) and a **flagged contradiction** (hardcoded rate literals vs. the dated-rate-authority invariant). Surface these; never quietly pick a side on a statutory question.
- **Simplicity First** — Minimum code that solves the problem; nothing speculative. No unrequested features, abstractions, flexibility, or error handling for impossible cases. Respect the hard scope line: **v1.0R is monthly payroll only** — do not build deferred v1.1R+ items (extra pay periods, ZV sick pay, CSV exports, loan deductions, gevarenklasse model) early.
- **Surgical Changes** — Touch only what you must; clean up only your own mess; match existing style. Don't refactor working code or "improve" unrelated rules. This reinforces the **layer boundaries** and the **never-gate list**: editing a premium rule must not perturb a shared base (`*_PREM_INC`, `TAX_INC`, `LOONBEL_RAW`, `NET`, `TOTAL_ER_COST`).
- **Goal-Driven Execution** — Define success criteria, then loop until verified. The PRD's **acceptance criteria** are the verification target: calculations reconcile to the official 2026 publications within XCG 0.02, every run close yields a balanced `account.move`, disabling a premium yields `0.00` without disturbing NET, and rates update with no code deploy.
