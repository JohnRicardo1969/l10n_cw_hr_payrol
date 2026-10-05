# Story 1.4: Dated statutory data models and lookup methods

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->
<!-- Ultimate context engine analysis completed - comprehensive developer guide created (batch-created 2026-07-08 from epics EN v1.0D + ARCHITECTURE-SPINE + PRD v3.0D + Story 1.1 learnings). -->

## Story

As a payroll admin,
I want dated, append-only statutory data models with deterministic lookup methods,
so that rates and tables are maintained as data and read reproducibly by effective date.

## Acceptance Criteria

1. **Given** the models, **Then** `hr.svb.parameters` (one per year), `hr.tax.bracket` (dated, `tax_type`-keyed), and `hr.loonbelasting.tabel` (header) + `hr.loonbelasting.tabel.lijn` (rows) exist. *(FR017, AR006, AR024)*
2. **Given** a `tax_type` and a date, **When** `compute_tax` is called, **Then** it returns the dated Belastingdienst scalar rounded to 2 decimals; `lookup_marginal_rate` returns the single bijzondere band rate; `lookup_loonbelasting` returns the periodic raw loonbelasting. *(AR012)*
3. **Given** multiple lb-tabel headers for a `period_type`+`year`, **When** `lookup_loonbelasting` runs for a date, **Then** it selects active headers for the payslip year or the year before with `valid_from ≤ date_to` and `valid_to` empty or `≥ date_to`, ordered by `year` desc, then `valid_from` desc, then `id` desc — the prior year's still-open table is used only until the new year's table is uploaded. *(AR024, FR031; decided 2026-10-04)*
4. **Given** a required record or table missing for the effective date, **Then** a `UserError` is raised (fail-loud), never a silent 0. For the lb-tabel, "missing" means neither a current-year header nor a still-open prior-year header qualifies. *(AR021)*
5. **Given** a superseded value, **Then** it is closed via `valid_to` and never deleted (append-only), and schema changes ship migrations preserving history. *(AR023)*
6. **Given** national statutory data, **Then** these models are global (no `company_id`). *(AR022)*

## Tasks / Subtasks

- [ ] **Task 1 — `hr.tax.bracket` model + methods** (AC: 1, 2, 4, 5, 6)
  - [ ] Create `models/hr_tax_bracket.py`: fields `name`, `sequence`, `income_from` (Float), `income_to` (Float, 0 = no ceiling), `rate` (Float, percentage), `valid_from` (Date, required), `valid_to` (Date, nullable), `tax_type` (Selection: `bijzondere_beloning`, `basiskorting`, `verwervingskosten`, `alleenverdienerstoeslag`, `kindertoeslag`, `ouderentoeslag`), `active` (Boolean). Inherit `mail.thread` (NFR002 audit).
  - [ ] `@api.model compute_tax(tax_type, date)` → the dated **scalar** (flat amount/rate) for `tax_type` effective on `date`, `round(x, 2)`. **No `today()` default — `date` is required** (AD-17). Missing record → `UserError` naming the `tax_type` and date (AD-18).
  - [ ] `@api.model lookup_marginal_rate(jaarloon, tax_type, date)` → the **single band rate** whose range contains `jaarloon`: match `income_from ≤ jaarloon < income_to`, `income_to = 0` = top band uncapped; **no accumulation**. Same dated selection + fail-loud.
- [ ] **Task 2 — `hr.svb.parameters` model** (AC: 1, 4, 5, 6)
  - [ ] Create `models/hr_svb_parameters.py`: per-year header — `year` (Integer), `valid_from`, `valid_to` (nullable), `active`; rate fields (all **percentages**, e.g. `bvz_er = 9.3`): `aov_er`, `aov_emp`, `aww_er`, `aww_emp`, `bvz_er`, `bvz_emp`, `avbz_er`, `avbz_emp`, `zv`, `bvz_pensioner`, `bvz_self`, `aov_surcharge_rate`; annual ceilings `aov_aww_grens`, `bvz_grens`, `avbz_grens`; monthly cap `zv_ov_loongrens_month`. Inherit `mail.thread`. SQL constraint: unique `year` per version window is NOT required (corrections allowed) — do not over-constrain.
  - [ ] Selection helper `@api.model get_params(date)`: among `active=True` records with `year = date.year` AND `valid_from ≤ date` AND (`valid_to` null or `≥ date`), pick latest by `valid_from desc, id desc`. **No prior-year fallback** — a January payslip with no current-year record fails loud (`UserError`) (AD-22).
- [ ] **Task 3 — `hr.loonbelasting.tabel` (+ `.lijn`) model + lookup** (AC: 1, 2, 3, 4, 5, 6)
  - [ ] Create `models/hr_loonbelasting_tabel.py`: header fields `name`, `period_type` (Selection; v1.0R: `maand`; keep `week`/`dag`/`halvedag`/`quincena`/`kwartaal` values in the selection for v1.1R), `year` (Integer), `valid_from`, `valid_to` (nullable), `active`, `above_ceiling_rate` (Float — 46.5 for 2026; a **header field**, never a code literal), `lijn_ids` One2many. Row model `hr.loonbelasting.tabel.lijn`: `tabel_id`, `wage_from` (Float), `loonbelasting` (Float); unique `(tabel_id, wage_from)`.
  - [ ] `@api.model lookup_loonbelasting(wage, period_type, date)`: select header per AC3 (active, `period_type` match, `year in (date.year, date.year - 1)`, `valid_from ≤ date`, `valid_to` null or `≥ date`, order `year desc, valid_from desc, id desc`, limit 1 — the prior-year header is the fallback until the new year's table is uploaded; decided 2026-10-04, AD-20); lookup key `wage_from = floor(wage / step) * step` (maand step = 5.00); above table ceiling: `ceiling_tax + (wage − ceiling_wage) × above_ceiling_rate/100`; return `round(x, 2)`. Missing header or row → `UserError` naming `period_type` + date (AD-18).
- [ ] **Task 4 — Views, menu, access** (supports FR017 rate maintenance)
  - [ ] List/form views for all three models + menu Salarisadministratie → Configuratie → Tarieven (Dutch labels). Use Odoo 19's default look: no wrapper class or custom styling (AD-15, decided 2026-10-05, superseding the `.cw_theme_prl10n` wrapper).
  - [ ] Add `ir.model.access` rows (per 1.3 convention): Payroll Manager = CRUD; Payroll User = read; others = none.
  - [ ] Wire new files into `models/__init__.py` and the manifest `data` list.
- [ ] **Task 5 — Tests (first `tests/` package)** (AC: 2, 3, 4)
  - [ ] Create `tests/__init__.py` + `tests/test_statutory_lookups.py` (`TransactionCase`): scalar lookup by date window; marginal-rate band edges (`income_from ≤ x < income_to`, top band `income_to=0`); lb-tabel version selection (two headers same year → latest `valid_from` wins; tie → highest `id`); lb-tabel prior-year fallback (January 2027 with only a still-open 2026 header → 2026 table used; once a 2027 header exists → 2027 wins; 2026 header closed via `valid_to` → `UserError`; only a 2025 header in 2027 → `UserError`); above-ceiling formula; `UserError` on missing record for all three lookups; no-prior-year-fallback for `get_params`.

## Dev Notes

### Read contracts (AD-5/AD-20/AD-22 — binding; two authors must encode identically)

- **Three stores by shape:** SVB rates+ceilings → one per-year `hr.svb.parameters` record (each ceiling stored exactly once); bijzondere band records + Belastingdienst scalars → `hr.tax.bracket`; loonbelasting → `hr.loonbelasting.tabel` (the Schijventarief is NOT the withholding instrument and must never be modeled).
- **Selection rule — shared core, one deliberate difference per store (decided 2026-10-04):** all three pick among active records valid on the effective date → `valid_from desc, id desc`; corrections are new records that win by upload order; no mandatory archiving of the old record. On top of that core:
  - `hr.svb.parameters`: `year = date.year` only — **no prior-year fallback** (AD-22).
  - `hr.loonbelasting.tabel`: `year in (date.year, date.year - 1)`, ordered `year desc` first — the prior year's still-open table is used until the new year's table is uploaded (AD-20, FR031). Older or closed tables → `UserError`.
  - `hr.tax.bracket`: no year field — a scalar carries over only while its own `valid_to` is open.
  - Do not harmonise these three rules; the asymmetry is a product-owner decision.
- **Effective date:** always passed explicitly; in payroll context it is `payslip.date_to` (AD-17). No method may default to `today()` — the v3.0D `compute_tax` defaulting to `today()` is an identified defect; do not copy it.
- **Data records hold only rates/ceilings/bounds — never arithmetic.** Capping, summing (e.g. `aov_emp + aww_emp`), and de-annualisation live in the salary rules (Epic 2), not in these models.
- **Rate unit:** every rate field is a percentage (9.3 means 9.3%); the consumer divides by 100. No fractions.
- **Append-only:** supersede = set `valid_to` + insert new `valid_from`; never delete. Superseded lb-tabel headers may be archived (`active=False`) once replaced but are retained. Enforce "never lose history" at review level; do not build a delete-blocking override unless trivial (`ondelete` guards on rows are fine).

### Model-shape notes

- `hr.tax.bracket` field shape comes from Tech Design §6.6 (table above §"SUPERSEDED" note) — but its `tax_type` list is the **post-AD-22 reduced set** (SVB values removed). The toeslag selection values: keep one value per toeslag type (alleenverdiener/kinder/ouderen) — the per-child breakdown (948/475/124/96) is seed detail for Story 1.5, stored as separate dated records or documented reference values; the **applied** personal toeslagen read from employee fields (Story 1.9/2.7).
- `hr.svb.parameters` field list comes from AD-22 verbatim (illustrative shape — you own the final shape, but keep the named fields the rule-to-field map expects: `AOV_AWW_EMP` reads `aov_emp + aww_emp`, etc.). The OV rate is NOT here (per-employer gevarenklasse on `hr.version`, Story 1.9); only the shared OV loongrens is here. No SVB benefit amounts, no Cessantia (permanently out of scope).
- `hr.loonbelasting.tabel` shape comes from AD-20 verbatim. Global scope — **no `company_id`** on any model in this story (AD-19). All three inherit `mail.thread`.
- **Layer:** all three are Localization-layer models (`models/hr_tax_bracket.py`, `hr_svb_parameters.py`, `hr_loonbelasting_tabel.py`) — they must not import Application/Reports code (AD-11).

### Migration discipline (AC5 / AR023)

This story creates the models fresh (no migration needed yet), but the convention starts here: any later schema change to these models ships an Odoo migration script preserving historical statutory records and closed YTD. Note it in each model's docstring.

### Previous story intelligence (Stories 1.1–1.3)

- Manifest data-list guardrail: add view/security XML entries only for files created in this story.
- Odoo 19 D1: no `hr.contract`; salary-rule localdict exposes `version`. Not directly touched here but the model docstrings/comments must not reference `hr.contract`.
- Security convention from 1.3: this story adds its own `ir.model.access` rows; groups exist as `group_l10n_cw_*`.
- Presentation: no theme. The `cw_theme_prl10n` theme from Story 1.2 was removed (decided 2026-10-05, AD-15); views use Odoo 19's default look, with no wrapper class.
- Verification protocol: dev-side `TransactionCase` tests may not be runnable in the sandbox (no Odoo core — verified in 1.1); write them anyway, document the run command, delegate execution to PO if needed.

### Project Structure Notes

- New files: `models/hr_tax_bracket.py`, `models/hr_svb_parameters.py`, `models/hr_loonbelasting_tabel.py`, `views/hr_tax_bracket_views.xml`, `views/hr_svb_parameters_views.xml`, `views/hr_loonbelasting_tabel_views.xml`, `views/hr_payroll_menu.xml`, `tests/__init__.py`, `tests/test_statutory_lookups.py`; modified: `models/__init__.py`, `security/ir.model.access.csv`, `__manifest__.py`, `i18n/nl.po` (new strings).
- Variance vs Tech Design §13: `hr_svb_parameters.py` and `hr_loonbelasting_tabel.py` are Spine additions (AD-20/AD-22) — intended.

### Testing standards

- `odoo.tests.TransactionCase`, tagged post-install where appropriate; discovered from `tests/`. Run: `odoo-bin -d cw_test -u l10n_cw_hr_payroll --test-enable --test-tags /l10n_cw_hr_payroll --stop-after-init`.

### References

- [Source: _bmad-output/planning-artifacts/Odoo Module Design Epics - EN - v1.0D.md#Story 1.4; #AR006, AR012, AR021, AR022, AR023, AR024]
- [Source: _bmad-output/planning-artifacts/architecture/architecture-l10n_cw_hr_payrol-2026-06-25/ARCHITECTURE-SPINE.md#AD-5, AD-17, AD-18, AD-19, AD-20, AD-22]
- [Source: docs/prd/PRD - v3.0D.md#hr.tax.bracket; #2026 Loonbelasting Table; #Rate Update Procedure]
- [Source: docs/tech_design_l10n_cw_hr_payroll_v3.0D.txt#6.6 hr.tax.bracket (+ SUPERSEDED note), #Listing 5 compute_tax]
- [Source: _bmad-output/implementation-artifacts/1-1-greenfield-module-skeleton-and-manifest.md#Dev Notes]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2026-10-04: AD-20 lb-tabel selection amended (PO decision): prior-year still-open table is the fallback until the new year's table is uploaded; `year = date.year` replaced by `year in (date.year, date.year - 1)` with `year desc` ordering. Updated AC3, AC4, Task 3 lookup bullet, Task 5 tests, and the Dev Notes selection rule. SVB `get_params` keeps no prior-year fallback (AD-22).
