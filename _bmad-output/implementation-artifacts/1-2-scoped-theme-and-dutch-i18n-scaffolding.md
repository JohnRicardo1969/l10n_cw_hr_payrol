# Story 1.2: Scoped theme and Dutch i18n scaffolding

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->
<!-- Ultimate context engine analysis completed - comprehensive developer guide created (batch-created 2026-07-08 from epics EN v1.0D + ARCHITECTURE-SPINE + PRD v3.0D + Story 1.1 learnings). -->

## Story

As a payroll admin,
I want the module's own screens styled with the `cw_theme_prl10n` theme and a Dutch interface,
so that the module looks consistent and reads in Dutch without altering Odoo's standard pages.

## Acceptance Criteria

1. **Given** the manifest `assets` entry, **When** the backend loads, **Then** `static/src/scss/cw_theme_prl10n.scss` is bundled into `web.assets_backend` (not the data list). *(UX-DR001, AR014)*
2. **Given** any theme rule, **Then** it is nested under the `.cw_theme_prl10n` wrapper and applied only to the module's own model screens; extended Odoo views (Employee, Contract/Version, Salary Rule) render unchanged. *(UX-DR002)*
3. **Given** light and dark mode, **Then** the pastel palette is defined as CSS variables under `:root` and `.o_dark_mode`. *(UX-DR003)*
4. **Given** `i18n/nl.po`, **Then** the module's UI strings have Dutch translations and statutory terms keep their official form (e.g. `basiskorting`, not `basisaftrek`). *(AR016)*

## Tasks / Subtasks

- [ ] **Task 1 — Create the scoped SCSS theme file** (AC: 2, 3)
  - [ ] Create `l10n_cw_hr_payroll/static/src/scss/cw_theme_prl10n.scss` (replaces the `.gitkeep` placeholder in `static/src/scss/`).
  - [ ] Define the pastel palette tokens as CSS variables: light mode under `:root`, dark mode under `.o_dark_mode` (Odoo's dark-mode class). Copy the palette values (lavender/violet accent; mint/peach/sky/rose support tints) from the reference module — do NOT add any dependency on it.
  - [ ] Nest **every** style rule under the single wrapper class `.cw_theme_prl10n`. Zero rules outside the wrapper.
- [ ] **Task 2 — Register the asset bundle in the manifest** (AC: 1)
  - [ ] Add to `__manifest__.py`: `'assets': {'web.assets_backend': ['l10n_cw_hr_payroll/static/src/scss/cw_theme_prl10n.scss']}`.
  - [ ] Do NOT add the SCSS to the `data` list; `data` stays `[]` in this story.
- [ ] **Task 3 — Dutch i18n scaffolding** (AC: 4)
  - [ ] Create `l10n_cw_hr_payroll/i18n/nl.po` with a valid PO header (module has almost no translatable strings yet — this establishes the file and the workflow; later stories extend it as views/models add strings).
  - [ ] Document the statutory-term rule in a comment block in the PO file: statutory terms keep their official form (`basiskorting`, `verwervingskosten`, `loonbelasting`, `bijzondere beloningen`, `beschikking` — never "translated away").
- [ ] **Task 4 — Verify** (AC: 1, 2)
  - [ ] Dev-side: SCSS compiles (no syntax errors); manifest still parses via `ast.literal_eval`; every rule verified under `.cw_theme_prl10n` (grep for top-level selectors).
  - [ ] Install smoke test (`-u l10n_cw_hr_payroll`) — if no Odoo runtime is available in the sandbox, document the command and delegate the live run to the PO (same protocol as Story 1.1).
  - [ ] Verify a standard Odoo page (e.g. Employees form) renders without the wrapper class present anywhere in its DOM.

## Dev Notes

### Critical constraints (AD-15 — Scoped presentation theming)

- The theme ships as an **in-module SCSS bundle** registered via the manifest `assets` key into `web.assets_backend` — **never** the `data` list, and **no theme-module dependency** in `depends`.
- Every rule scoped under **one** wrapper class `.cw_theme_prl10n`. The wrapper is applied **only** to the module's own custom-model views (`hr.tax.bracket`, `hr.wage.component.set`, `hr.employee.wage.line`, CW-owned payslip/run views) — **never** on inherited Odoo-model views (`hr.employee`, `hr.version`, `hr.salary.rule`). Note: those module views **do not exist yet** — they arrive in Stories 1.4/1.7/1.9/1.10. This story delivers the stylesheet + tokens + registration; each later view story applies the wrapper class to its own views. State this in the SCSS header comment so no future dev "helpfully" globalizes the styles.
- Theming is presentation only — it computes no statutory amount (AD-11).
- Reference palette (read-only, not a dependency): `/home/nroosje/dev/odoo-sh/odoo-cbw-ent/service-business-suite/cw_theme`. Copy values; never import or depend.
- Portal styling (`.cw-portal`) is **deferred** (UX-DR004, OQ-01) — backend only in v1.0R. Do not create portal SCSS.

### Previous story intelligence (Story 1.1)

- Manifest currently has `data: []` and **no `assets` key** — that was deliberate (install-ordering guardrail: never reference a file that doesn't exist). This story creates the SCSS **first**, then adds the `assets` entry — same commit, safe order.
- Manifest key discipline: `countries: ['cw']` (list), version `19.0.0.1.0`, 5 depends, author `Caribware`. Re-assert via `ast.literal_eval` after editing (pattern established in 1.1 Debug Log).
- No Odoo core/Postgres in the dev sandbox (verified in 1.1): live install verification is delegated to the PO; dev-side verification is static. Reference checkout for conventions (read-only): `/home/nroosje/dev/odoo-sh/enterprise-19.0/`.
- Odoo 19 note: there is no `hr.contract` — the "Contract" screens are `hr.version` (D1, 2026-07-07). AC2's "extended Odoo views" list therefore means Employee / Version / Salary Rule views.

### i18n mechanics

- Odoo loads `i18n/<lang>.po` automatically at module install/update when the language is active. File must be named `nl.po` (or `nl_NL.po` — use plain `nl.po`, matching CLAUDE.md's `i18n/nl.po` convention and the tech-design tree).
- UI strings and menus for this module are authored in Dutch at the source level per CLAUDE.md (e.g. Salarisadministratie → Configuratie → Tarieven), so the PO file mostly covers residual English source strings. Keep the file valid even when nearly empty.

### Project Structure Notes

- Files touched: `static/src/scss/cw_theme_prl10n.scss` (new), `i18n/nl.po` (new), `__manifest__.py` (assets key added). Remove the two `.gitkeep` placeholders these replace.
- Matches Tech Design §13 tree (`i18n/nl.po`) + Spine AD-15 (`static/src/scss/cw_theme_prl10n.scss`; the SCSS/assets entry is a Spine addition to §13 — intended, not a conflict).

### Testing standards

- No `tests/` package yet (no Python behavior in this story). Verification is static (SCSS syntax, manifest parse, wrapper-scoping grep) plus the PO-delegated install smoke test: `odoo-bin -d cw_test --addons-path=<community>/addons,/home/nroosje/dev/odoo-sh/enterprise-19.0,/home/nroosje/dev/odoo-poc/l10n_cw_hr_payrol -u l10n_cw_hr_payroll --stop-after-init` then visually confirm standard pages are unstyled.

### References

- [Source: _bmad-output/planning-artifacts/Odoo Module Design Epics - EN - v1.0D.md#Story 1.2; #UX Design Requirements UX-DR001..004; #AR016]
- [Source: _bmad-output/planning-artifacts/architecture/architecture-l10n_cw_hr_payrol-2026-06-25/ARCHITECTURE-SPINE.md#AD-15, AD-11]
- [Source: _bmad-output/implementation-artifacts/1-1-greenfield-module-skeleton-and-manifest.md#Dev Notes (install-ordering guardrail), #Debug Log]
- [Source: CLAUDE.md#Conventions when code is added (Dutch UI strings, statutory terms)]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
