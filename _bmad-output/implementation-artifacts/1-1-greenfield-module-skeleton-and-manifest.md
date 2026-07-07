---
baseline_commit: c136873ab959b86f7ee62838b06009e414c4bc09
---

# Story 1.1: Greenfield module skeleton and manifest

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a payroll admin,
I want to install the `l10n_cw_hr_payroll` module on Odoo 19 Enterprise,
so that the Curaçao payroll framework is available without errors.

## Acceptance Criteria

1. **Given** a clean Odoo 19 Enterprise database with `hr_payroll` installed, **When** I install `l10n_cw_hr_payroll`, **Then** it installs without error and reports version `19.0.0.1.0`, country `cw`, license `OPL-1`, `application=False`, and `auto_install=False`. *(AR014)*
2. **Given** the manifest, **When** inspected, **Then** `depends` = `hr, hr_contract, hr_holidays, hr_payroll, hr_payroll_account, hr_attendance` with **no theme dependency added**. *(AR014)*
3. **Given** the package layout, **When** inspected, **Then** directories follow the three-layer boundaries (Localization ← Application ← Reports) per Tech Design §13 and AD-11. *(AR001)*
4. **Given** the freshly installed skeleton, **Then** no statutory rate, ceiling, or threshold is hard-coded in Python. *(AR006)*

## Tasks / Subtasks

- [x] **Task 1 — Create the package skeleton and `__init__.py` wiring** (AC: 3)
  - [x] Create the module root `l10n_cw_hr_payroll/` with `__init__.py` and `__manifest__.py`.
  - [x] Create the layer directories with their `__init__.py` where Python is imported: `models/`, `wizard/`. Create empty non-Python asset dirs: `data/`, `views/`, `report/`, `security/`, `static/src/scss/`, `i18n/` (each seeded with a `.gitkeep`).
  - [x] Root `__init__.py` imports `models` and `wizard`; `models/__init__.py` and `wizard/__init__.py` present but empty (models arrive in Stories 1.4/1.7/1.9/2.x).
- [x] **Task 2 — Author `__manifest__.py` with correct metadata + depends** (AC: 1, 2)
  - [x] Set `name` `'Payroll — Curaçao'`, `version` `'19.0.0.1.0'`, `category` `'Human Resources/Payroll'` (PO decision 2026-07-07 — Odoo convention, official-localization track), `summary`, `author`, `license` `'OPL-1'`.
  - [x] Set `countries` = `['cw']` (Odoo 17+/19 manifest key; renders as country `cw`).
  - [x] Set `depends` = the six modules exactly, **no theme module**.
  - [x] Set `installable = True`, `application = False`, `auto_install = False`.
  - [x] `data` list empty; no `assets` entry yet (guardrail honored).
- [x] **Task 3 — Confirm three-layer boundary mapping** (AC: 3)
  - [x] Directory-to-layer mapping (AD-11) respected; boundary documented in `__manifest__.py` comments and this story's Dev Notes. No cross-layer imports exist yet.
- [x] **Task 4 — Verify clean install and the no-hardcode principle** (AC: 1, 4)
  - [x] Live install on a clean Odoo 19 Enterprise DB → **delegated to PO** (user instruction 2026-07-07: "I will take care of that"). Dev-side scope complete; PO confirms the Apps entry shows version `19.0.0.1.0`, license `OPL-1`, country `cw`, not an Application.
  - [x] Confirmed no Python statutory literals (grep of `*.py` — skeleton has none). *(AC4 met)*
  - [x] Manifest validity asserted statically via `ast.literal_eval` (all AC1/AC2 fields — see Debug Log).
- [x] **Task 5 — Verification: live install smoke-test** (AC: 1)
  - [x] `odoo-bin -i l10n_cw_hr_payroll -d <db> --test-enable --stop-after-init` → **delegated to PO** (runs in own Odoo 19 Enterprise env; command documented in Completion Notes). Not executable in this sandbox (no Odoo core/Postgres).

## Dev Notes

### What this story is (and is not)

This is the **greenfield skeleton only**: package structure + a valid, installable `__manifest__.py`. It stands up **no models, data, views, security, or reports** — those arrive in later Epic 1/2 stories. Success = the empty-but-valid module installs cleanly on Odoo 19 Enterprise and declares the correct metadata. [Source: epics#Story 1.1; AR001 — greenfield, no starter template]

### Platform & greenfield constraints

- **Odoo 19 Enterprise on Odoo.sh / self-hosted Enterprise. SaaS is not supported** (custom modules + Python salary rules required). [Source: PRD#Platform Decision]
- Requires the Enterprise modules `hr_payroll` and `hr_payroll_account` (not in Community). [Source: PRD#Platform Decision]
- No starter template — fresh module built by hand. [Source: epics#AR001]

### `__manifest__.py` — authoritative fields

```python
{
    'name':      'Payroll — Curaçao',
    'version':   '19.0.0.1.0',
    'category':  'Human Resources/Payroll',  # PO decision 2026-07-07: Odoo convention
    'summary':   'Curaçao payroll localization: loonbelasting, SVB premiums, three-tier wage model',
    'author':    '[COMPANY]',
    'license':   'OPL-1',
    'countries': ['cw'],
    'depends': [
        'hr', 'hr_contract', 'hr_holidays',
        'hr_payroll', 'hr_payroll_account', 'hr_attendance',
    ],
    'data': [],          # grows per later story — never list a file that doesn't exist yet
    'installable': True,
    'application': False,
    'auto_install': False,
}
```
[Source: docs/tech_design_l10n_cw_hr_payroll_v3.0D.txt#Key __manifest__.py Fields; epics#AR014]

- **Manifest key is `countries` (list), not `country`** in Odoo 17+/19. The CLAUDE.md phrasing "country `cw`" refers to the resulting localization country; encode it as `'countries': ['cw']`. [Source: tech_design#Key __manifest__.py Fields]
- **No theme dependency.** The scoped theme (`cw_theme_prl10n`) is bundled as an in-module SCSS asset in **Story 1.2**, not as a module `depends`. Do not add it here. [Source: epics#Story 1.2, AR014, UX-DR001]

### 🚩 Install-ordering guardrail (highest-value note for the dev)

The Tech Design §13 manifest shows a **fully populated** `data` list (security, structure, salary rules, tax brackets, views, reports) and the §13 file tree lists models like `hr_tax_bracket.py`. **That is the end-state manifest, not this story's.** If you copy the full `data`/`assets` list now, install fails because those XML/CSV/SCSS files don't exist yet. For Story 1.1:
- Keep `data = []` (or only genuinely-present files).
- Add **no** `assets` entry yet (Story 1.2 adds `web.assets_backend` → `static/src/scss/cw_theme_prl10n.scss` once the SCSS exists).
- Each later story appends its own `data`/`assets`/model entries when it creates the corresponding files.

### Three-layer boundary mapping (AD-11 / AR001)

Dependencies point **inward toward Localization**: Localization ← Application ← Reports. A report must never recompute a statutory amount. Map the §13 Odoo-convention dirs onto the layers:

| Layer | Owns | Dirs (as they get populated) |
|-------|------|------------------------------|
| **Localization** (statutory truth) | salary-rule extension, `CWMONTHLY`/`CWSTAFF`, CW rules, `hr.tax.bracket`, `hr.svb.parameters`, `hr.loonbelasting.tabel`, employee toeslag / contract OV% fields, seed data | `models/` (statutory), `data/` |
| **Application** (config/workflow) | wage-component set (+line), employee wage line, YTD, apply wizard, views, menus, security | `models/` (app), `wizard/`, `views/`, `security/` |
| **Reports** (read-only) | QWeb PDF + CSV; compute nothing | `report/` |

Note the Spine adds two models beyond §13's tree — `hr.svb.parameters` (AD-22) and `hr.loonbelasting.tabel` (AD-20) — created in Story 1.4, not here. [Source: ARCHITECTURE-SPINE.md#AD-11, AD-20, AD-22; CLAUDE.md#Architecture invariants]

### Conventions to honor now (cheap to get right at skeleton stage)

- Manifest version `19.0.0.1.0` (dev line; first production is `19.0.1.0.0`). [Source: CLAUDE.md; memory: versioning-scheme]
- UI strings/menus are Dutch (Salarisadministratie → Configuratie → …); statutory terms keep official form (`basiskorting`, not `basisaftrek`). Not exercised in this story but sets the naming baseline. [Source: CLAUDE.md]
- No statutory literals in Python anywhere (AD-5). Trivial now; stays binding. [Source: epics#AR006]

### Testing standards

- Odoo modules are tested with `odoo.tests` (`TransactionCase` / `HttpCase`) discovered from a `tests/` package. **No unit tests ship in this story** — there is no behavior yet.
- Verification for 1.1 is an **install smoke test**: `-i l10n_cw_hr_payroll --test-enable --stop-after-init` on a clean Enterprise DB returns success, and the Apps UI shows the correct metadata. A `tests/` package is introduced by the first story that adds behavior (Story 1.4 onward).

### Project Structure Notes

- Follows the Tech Design §13 file tree exactly for directory names; only the **manifest `data`/`assets` population differs by design** (incremental per story, per the install-ordering guardrail above).
- Variance vs §13: two Localization models (`hr.svb.parameters`, `hr.loonbelasting.tabel`) and the `assets` bundle are Spine additions (AD-20/AD-22, UX-DR001) that land in Stories 1.2/1.4 — not a conflict, just later.

### References

- [Source: _bmad-output/planning-artifacts/Odoo Module Design Epics - EN - v1.0D.md#Story 1.1: Greenfield module skeleton and manifest]
- [Source: _bmad-output/planning-artifacts/Odoo Module Design Epics - EN - v1.0D.md#Additional Requirements — AR001, AR014, AR006]
- [Source: docs/tech_design_l10n_cw_hr_payroll_v3.0D.txt#Module File Structure]
- [Source: docs/tech_design_l10n_cw_hr_payroll_v3.0D.txt#Key __manifest__.py Fields]
- [Source: _bmad-output/planning-artifacts/architecture/architecture-l10n_cw_hr_payrol-2026-06-25/ARCHITECTURE-SPINE.md#AD-11, AD-20, AD-22]
- [Source: docs/prd/PRD - v3.0D.md#Platform Decision]
- [Source: CLAUDE.md#Conventions when code is added]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.8 (claude-opus-4-8) with 3 parallel Explore subagents (Enterprise-convention audit, environment probe, module-loading audit); Enterprise checkout `/home/nroosje/dev/odoo-sh/enterprise-19.0/` used strictly read-only as build reference.

### Debug Log References

- `py_compile` on all 4 `.py` files: OK.
- Manifest parsed via `ast.literal_eval`; all AC1/AC2 assertions PASS: version `19.0.0.1.0`, license `OPL-1`, `countries==['cw']`, `application=False`, `auto_install=False`, `installable=True`, `depends` == the exact six, no theme dependency, `data=[]`, no `assets` key.
- AC4 grep: no statutory numeric literals in any `.py` (only the version string).
- Convention audit vs 23 Enterprise `l10n_*_hr_payroll` manifests: `countries` list key correct (23/23 peers); `data: []` valid (Odoo only fails on *missing referenced* files); empty/comment-only sub-package `__init__.py` loads fine (peers ship empty inits, e.g. `l10n_et_reports/__init__.py`); `.gitkeep` placeholders inert (only manifest-listed files are loaded).
- Environment probe: no Odoo core on this machine (`import odoo` fails, no odoo-bin/community checkout), docker daemon permission-denied, no Postgres on :5432 → live install smoke-test NOT runnable in this sandbox.

### Completion Notes List

- Implemented the greenfield skeleton exactly per Dev Notes: module root `l10n_cw_hr_payroll/` inside the repo (repo dir `l10n_cw_hr_payrol` is the addons-path container; note the repo name has one `l`, the module the correct `ll`), manifest with the authoritative field set, `models/`+`wizard/` Python packages (comment-only inits), and the six asset dirs seeded with `.gitkeep`.
- Install-ordering guardrail honored: `data: []`, no `assets` entry; inline manifest comment explains why (a manifest referencing a not-yet-existing file breaks install).
- **AC3, AC4: verified.** **AC1, AC2: all statically verifiable properties verified**; the *live* "installs without error on a clean Odoo 19 Enterprise DB" run is **pending the user's environment** (sandbox has no Odoo core/Postgres). Command to run there (adjust community path/db):
  `odoo-bin -d cw_test --addons-path=<community>/addons,/home/nroosje/dev/odoo-sh/enterprise-19.0,/home/nroosje/dev/odoo-poc/l10n_cw_hr_payrol -i l10n_cw_hr_payroll --test-enable --stop-after-init`
- **Finding RESOLVED (PO decision 2026-07-07):** category changed to `Human Resources/Payroll` — the convention used by all 42 shipped payroll localizations — so the module can join the official payroll-localization track later. Manifest, CLAUDE.md, and PRD updated together; the frozen v3.0D tech design and historical review artifacts intentionally left as-is (superseded, per the Spine's "v3.0D literals are indicative only").
- License `OPL-1` confirmed valid for third-party code (shipped `l10n_ec_reports` uses it); version `19.0.0.1.0` valid (Odoo keeps strings already prefixed `19.0.`), matches the project dev-versioning convention.

### File List

- `l10n_cw_hr_payroll/__manifest__.py` (new)
- `l10n_cw_hr_payroll/__init__.py` (new)
- `l10n_cw_hr_payroll/models/__init__.py` (new)
- `l10n_cw_hr_payroll/wizard/__init__.py` (new)
- `l10n_cw_hr_payroll/data/.gitkeep` (new)
- `l10n_cw_hr_payroll/views/.gitkeep` (new)
- `l10n_cw_hr_payroll/report/.gitkeep` (new)
- `l10n_cw_hr_payroll/security/.gitkeep` (new)
- `l10n_cw_hr_payroll/static/src/scss/.gitkeep` (new)
- `l10n_cw_hr_payroll/i18n/.gitkeep` (new)

## Change Log

- 2026-07-07: Story 1.1 implementation — module skeleton + manifest created; Tasks 1–3 complete and statically verified; Tasks 4–5 (live Odoo 19 Enterprise install smoke-test) blocked pending user environment (no Odoo core/Postgres in sandbox). Category-convention finding recorded for review.
- 2026-07-07: PO decision — manifest category changed to `Human Resources/Payroll` (Odoo payroll-localization convention; keeps official-localization track open). Manifest + CLAUDE.md + PRD updated together; manifest re-asserted PASS.
- 2026-07-07: PO took ownership of the live install smoke-test (Tasks 4–5 delegation). Dev work complete; story moved to `review`. If the PO's install run surfaces an error, the story returns to `in-progress` for fixes.
