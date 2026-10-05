# Deferred Work

## Deferred from: code review of 1-1-greenfield-module-skeleton-and-manifest (2026-07-07)

- "Zuivere opbrengst" citation nuance: the PRD Steps 2/5 legal parenthetical cites *zuivere opbrengst van arbeid* to justify not deducting verwervingskosten from the premie-loon, but "zuiver" conventionally means net of acquisition costs. The AD-14 base decision stands (PO-confirmed; SVB flat-rate-on-brutoloon practice); the citation wording may deserve PO legal refinement.
- Repo/project name `l10n_cw_hr_payrol` (one *l*) vs module `l10n_cw_hr_payroll` — the typo lives in the repo directory name and propagates into `_bmad/bmm/config.yaml` `project_name` and sprint-status metadata. Renaming the repo is the user's call; tooling matching on project name should be aware.
- `countries: ['cw']` hides the module from the Apps list on databases whose company country is not Curaçao — expected Odoo localization behavior; document "install via CLI `-i l10n_cw_hr_payroll` or set the company country first" in onboarding notes.

## Deferred from: code review of 1-2-scoped-theme-and-dutch-i18n-scaffolding (2026-10-05)

*Theme items obsolete since 2026-10-05: the theme was removed (AD-15). Only the `nl.po` Dutch-source item still applies.*

- Muted text token `--cw-prl10n-text-muted: #9a93b5` on a white card is about 2.9:1, below WCAG AA (4.5:1). The palette was copied from the `cw_theme` reference; changing it is a design call for the PO.
- UX-DR002 scopes the theme to "CW-owned payslip/run views and reports", but the SCSS is only in `web.assets_backend`/`web.assets_web_dark`. QWeb PDF reports use the report bundles, so Story 4.1 must register the theme (and tokens) in the report asset bundle if reports are to be themed.
- `nl.po` notes that UI strings are written in Dutch at the source (CLAUDE.md convention). Odoo's i18n model expects English source terms; with Dutch sources, any other installed language falls back to Dutch and `nl.po` stays mostly empty. Revisit if the module ever targets the official localization track or a second language.
