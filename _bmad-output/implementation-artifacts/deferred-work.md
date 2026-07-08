# Deferred Work

## Deferred from: code review of 1-1-greenfield-module-skeleton-and-manifest (2026-07-07)

- "Zuivere opbrengst" citation nuance: the PRD Steps 2/5 legal parenthetical cites *zuivere opbrengst van arbeid* to justify not deducting verwervingskosten from the premie-loon, but "zuiver" conventionally means net of acquisition costs. The AD-14 base decision stands (PO-confirmed; SVB flat-rate-on-brutoloon practice); the citation wording may deserve PO legal refinement.
- Repo/project name `l10n_cw_hr_payrol` (one *l*) vs module `l10n_cw_hr_payroll` — the typo lives in the repo directory name and propagates into `_bmad/bmm/config.yaml` `project_name` and sprint-status metadata. Renaming the repo is the user's call; tooling matching on project name should be aware.
- `countries: ['cw']` hides the module from the Apps list on databases whose company country is not Curaçao — expected Odoo localization behavior; document "install via CLI `-i l10n_cw_hr_payroll` or set the company country first" in onboarding notes.
