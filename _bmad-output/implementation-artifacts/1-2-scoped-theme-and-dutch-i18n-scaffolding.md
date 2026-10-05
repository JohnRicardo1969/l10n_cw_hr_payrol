---
baseline_commit: fbb8bf8513c3fbbfb25403d0093eaedd2754c6ed
---

# Story 1.2: Scoped theme and Dutch i18n scaffolding

Status: in-progress

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
   *Superseded 2026-10-04 (PO decision): Odoo 19 has no `.o_dark_mode` class — light values under `:root` in `cw_theme_prl10n.scss`, dark values under `:root` in `cw_theme_prl10n.dark.scss` registered in `web.assets_web_dark` (see epics UX-DR003, spine AD-15).*
4. **Given** `i18n/nl.po`, **Then** the module's UI strings have Dutch translations and statutory terms keep their official form (e.g. `basiskorting`, not `basisaftrek`). *(AR016)*

## Tasks / Subtasks

- [x] **Task 1 — Create the scoped SCSS theme file** (AC: 2, 3)
  - [x] Create `l10n_cw_hr_payroll/static/src/scss/cw_theme_prl10n.scss` (replaces the `.gitkeep` placeholder in `static/src/scss/`).
  - [x] Define the pastel palette tokens as CSS variables: light mode under `:root`, dark mode under `.o_dark_mode` (Odoo's dark-mode class). Copy the palette values (lavender/violet accent; mint/peach/sky/rose support tints) from the reference module — do NOT add any dependency on it.
  - [x] Nest **every** style rule under the single wrapper class `.cw_theme_prl10n`. Zero rules outside the wrapper.
- [x] **Task 2 — Register the asset bundle in the manifest** (AC: 1)
  - [x] Add to `__manifest__.py`: `'assets': {'web.assets_backend': ['l10n_cw_hr_payroll/static/src/scss/cw_theme_prl10n.scss']}`.
  - [x] Do NOT add the SCSS to the `data` list; `data` stays `[]` in this story.
- [x] **Task 3 — Dutch i18n scaffolding** (AC: 4)
  - [x] Create `l10n_cw_hr_payroll/i18n/nl.po` with a valid PO header (module has almost no translatable strings yet — this establishes the file and the workflow; later stories extend it as views/models add strings).
  - [x] Document the statutory-term rule in a comment block in the PO file: statutory terms keep their official form (`basiskorting`, `verwervingskosten`, `loonbelasting`, `bijzondere beloningen`, `beschikking` — never "translated away").
- [ ] **Task 4 — Verify** (AC: 1, 2)
  - [x] Dev-side: SCSS compiles (no syntax errors); manifest still parses via `ast.literal_eval`; every rule verified under `.cw_theme_prl10n` (grep for top-level selectors).
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

Claude Opus 5.5 (claude-opus-5-5)

### Debug Log References

- Static verification script (scratchpad `verify_1_2.py`, not shipped — the story has no Python behaviour and no `tests/` package): red run before implementation (5 FAIL), final run 25/25 PASS. Checks cover the manifest `assets` keys, `data == []`, the 1.1 manifest invariants (version, `countries`, 5 depends, no `hr_contract`), SCSS top-level blocks exactly `:root` + `.cw_theme_prl10n`, no `.o_dark_mode`, tokens namespaced `--cw-prl10n-*`, no reference-theme wrapper or import, the dark file containing only a `:root` block of token values that redefines exactly the 22 light tokens, the PO header (Language nl, UTF-8) and the statutory terms, and both `.gitkeep` placeholders removed.
- SCSS compile: both files compiled cleanly with dart-sass 1.x (`npx sass`, run from the scratchpad; nothing added to the repo). Every compiled selector starts with `.cw_theme_prl10n` or `:root`. All 55 `var(--cw-prl10n-…)` uses resolve to defined tokens.
- PO syntax: parsed with a stdlib parser (no `msgfmt`/`polib` in the sandbox) — one header entry, all lines valid.
- Dark-mode finding: `grep -r o_dark_mode` over enterprise-19.0 returns zero hits; Odoo 19 serves `web.assets_web_dark` (defined in `web_enterprise`), extended by `*.dark.scss` files (account_reports, sign). AC3's `.o_dark_mode` scope would never activate. The PO chose the Odoo 19 mechanism (2026-10-04).
- Static evidence for the standard-page subtask: the wrapper class `.cw_theme_prl10n` appears in no XML/JS in the module (no views exist yet), and the compiled CSS contains only `.cw_theme_prl10n`-scoped rules plus `:root` custom properties. The live render check is still the PO's.

### Completion Notes List

- Theme: `cw_theme_prl10n.scss` (in `web.assets_backend`) holds the light tokens under `:root` and every style rule under `.cw_theme_prl10n`. The palette and rules are copied from the Caribware `cw_theme` reference, with no dependency on it. The header comment forbids applying the wrapper to inherited Odoo views or moving rules outside it.
- Dark mode — **deviation from AC3 as written, PO-approved 2026-10-04:** dark token values live in `cw_theme_prl10n.dark.scss` under `:root`, registered in `web.assets_web_dark`, not under `.o_dark_mode` (that class does not exist in Odoo 19). Spec chain updated in the same session: spine AD-15 + memlog, epics EN/NL (UX-DR001, UX-DR003, Story 1.2 AC, glossary). This story file's AC text is left as written (the dev workflow may not edit ACs); the epics carry the corrected AC.
- Tokens are namespaced `--cw-prl10n-*` instead of the reference's `--cw-*`. Both themes write their tokens on `:root`, so identical names would let one module overwrite the other's colours when both are installed.
- i18n: `i18n/nl.po` is a valid header-only PO file. The module has no translatable strings yet (no views/models), so AC4's "UI strings have Dutch translations" holds vacuously for now; the file documents the statutory-term rule and the convention that later stories extend it.
- Note outside this repo: the `cw_theme` reference module has the same `.o_dark_mode` defect, so its dark palette never activates on Odoo 19.
- **Open — PO verification (live, same protocol as Story 1.1).** The install command alone proves little here: `--stop-after-init` never compiles asset bundles, because Odoo compiles SCSS with libsass only when a browser first requests a bundle. Steps:
  1. `odoo-bin -d cw_test --addons-path=<community>/addons,/home/nroosje/dev/odoo-sh/enterprise-19.0,/home/nroosje/dev/odoo-poc/l10n_cw_hr_payrol -u l10n_cw_hr_payroll --stop-after-init`, then start the server normally.
  2. Open the backend in light mode. In the browser console run `getComputedStyle(document.documentElement).getPropertyValue('--cw-prl10n-card-bg')` → expect `#ffffff`.
  3. Switch to dark mode and run it again → expect `#1d1a26`. This proves the dark file loads after the light tokens.
  4. In both modes, check the browser console and the server log for asset/SCSS errors, and confirm the Employees form looks unchanged (no wrapper class in its DOM).

  Task 4's install and standard-page subtasks stay unchecked until this is reported, so the story stays `in-progress`. Bundle order: `web_enterprise` (which defines `web.assets_web_dark`) is a transitive dependency through `hr_payroll`, so it loads before this module.

### File List

- `l10n_cw_hr_payroll/static/src/scss/cw_theme_prl10n.scss` (new)
- `l10n_cw_hr_payroll/static/src/scss/cw_theme_prl10n.dark.scss` (new)
- `l10n_cw_hr_payroll/i18n/nl.po` (new)
- `l10n_cw_hr_payroll/__manifest__.py` (modified — `assets` key)
- `l10n_cw_hr_payroll/static/src/scss/.gitkeep` (deleted)
- `l10n_cw_hr_payroll/i18n/.gitkeep` (deleted)
- `_bmad-output/planning-artifacts/architecture/architecture-l10n_cw_hr_payrol-2026-06-25/ARCHITECTURE-SPINE.md` (AD-15 dark-mode mechanism)
- `_bmad-output/planning-artifacts/architecture/architecture-l10n_cw_hr_payrol-2026-06-25/.memlog.md` (decision entry)
- `_bmad-output/planning-artifacts/Odoo Module Design Epics - EN - v1.0D.md` (UX-DR001, UX-DR003, Story 1.2 AC, glossary)
- `_bmad-output/planning-artifacts/Odoo Module Design Epics - NL - v1.0D.md` (same, NL)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (1-2 → in-progress)
- `_bmad-output/implementation-artifacts/1-2-scoped-theme-and-dutch-i18n-scaffolding.md` (this file)

## Change Log

- 2026-10-04: Implemented Tasks 1–3 and the dev-side part of Task 4. Dark mode moved from the `.o_dark_mode` class (AC3 as written) to a `cw_theme_prl10n.dark.scss` file in `web.assets_web_dark`, because Odoo 19 has no dark-mode class (PO decision; spine AD-15 and epics EN/NL updated). Added a dated supersession note under AC3 (PO-approved). The live install and render checks are open for the PO, so the status stays in-progress.
