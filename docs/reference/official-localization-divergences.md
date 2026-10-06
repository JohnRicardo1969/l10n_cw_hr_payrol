::: {custom-style="Title"}
l10n_cw_hr_payroll
:::
::: {custom-style="Subtitle"}
Divergences from Official Odoo Payroll Localizations
:::

This register lists every place where `l10n_cw_hr_payroll` knowingly differs from the [official localization checklist](official-localization-checklist.md). Each row says whether the difference is a decision we keep (Decided) or a question still waiting for a product-owner decision (Open), why, and what it would take to align with the shipped Odoo localizations. Baseline: Odoo 19.0 Enterprise. Created 2026-10-06.

`tools/check_l10n_conformance.py` reads the ID column of the register table to tell known divergences from new ones: a check that fails on an ID listed here is reported as known, anything else as new. Keep the table format intact:

- The first column holds exactly one check ID, written like `C-05`.
- The second column holds the status, exactly `Decided` or `Open`.
- One row per check ID; keep the table as the only table under "Register".

# Register

| ID | Status | Divergence | Reason / decision | Decided by, date | To align |
|---|---|---|---|---|---|
| C-05 | Decided | `license` is `OPL-1`, not `OEEL-1` | CLAUDE.md manifest convention sets license `OPL-1` | CLAUDE.md manifest convention | Change the licence only if Odoo takes the module over as an official localization |
| C-07 | Decided | `auto_install` is `False`; peers auto-install with `hr_payroll` | CLAUDE.md manifest convention: "installable, not auto-installed" | CLAUDE.md manifest convention | Set `auto_install: ['hr_payroll']` |
| C-08 | Decided | `version` is `19.0.0.1.0`, not `'1.0'` or absent (cosmetic) | CLAUDE.md manifest convention sets version `19.0.0.1.0`, the usual form for third-party modules | CLAUDE.md manifest convention | Use `'1.0'` or drop the key |
| C-40 | Decided | Rates live in own dated models (`hr.tax.bracket` and related), not in `hr.rule.parameter` | Rates are append-only dated data with granular per-insurance, per-payer types and a defined read contract per type; loonbelasting reads the period table directly (architecture spine AD-5, AD-20, AD-22) | Architecture spine AD-5, AD-20, AD-22 | Move all rates to `hr.rule.parameter` with `l10n_cw_*` codes (C-41) and read them via `payslip._rule_parameter()`; requires superseding AD-5, AD-20 and AD-22 |
| C-50 | Decided | The module defines four own roles under its own privilege | Curaçao payroll needs separate Medewerker, Accountant, Gebruiker and Manager roles (Story 1.3) | Story 1.3; PO decision 2026-10-06 | Drop the roles and rely on the `hr_payroll` groups only; Medewerker and Accountant access would need another solution |
| C-51 | Decided | Access rows on the core `hr.payslip` and `hr.payslip.run` models | Consequence of C-50: Medewerker and Accountant need read access to payslips and runs, which core grants only to payroll users | Story 1.3; PO decision 2026-10-06 | Align together with C-50 |
| C-52 | Decided | Two record rules on the core `hr.payslip` model, not only multi-company rules on own models | Consequence of C-50: own-payslip rule for Medewerker, all-payslips rule for Accountant | Story 1.3; PO decision 2026-10-06 | Align together with C-50 |
| C-60 | Decided | Source strings are Dutch, not English | UI strings and menus are Dutch for the Curaçao users; statutory terms keep their official form (CLAUDE.md) | CLAUDE.md, Dutch UI strings convention | Rewrite source strings in English and move the Dutch text into `i18n/nl.po` |
| C-06 | Open | `depends` lists `hr_payroll_account` and `hr_attendance`, plus `hr` and `hr_holidays`, which `hr_payroll` already brings in | Not decided; `hr_payroll_account` is tied to C-12 | | Drop the redundant `hr` and `hr_holidays`; decide whether `hr_attendance` is really needed; move `hr_payroll_account` out with C-12 |
| C-12 | Open | Accounting (journal posting, rule accounts) is planned inside the base module, not in a separate bridge | Not decided | | Split accounting into an auto-installing `l10n_cw_hr_payroll_account` module that depends on `hr_payroll_account`, a Curaçao chart-of-accounts module and this module; no `l10n_cw` chart module was found in Enterprise, and whether one exists in Community is unconfirmed |
| C-53 | Open | The record-rule file is not `noupdate="1"` | Deferred in the Story 1.3 review: decide before production | | Mark the record-rule file `noupdate="1"` |
| C-23 | Open | Applies later (planned design), spec decision: the append-only rate design (AD-5) may want `noupdate` on rate data, while peers never put `noupdate` on payroll logic | Not decided; decide together with C-36 | | Ship rules, categories and rates without `noupdate`, or record why rate data needs it |
| C-32 | Open | Applies later (planned design), spec decision: specs use `CWMONTHLY` for the structure type and `CWSTAFF` for the structure; peers put `<CC>MONTHLY` on the structure | Not decided | | Give the structure the code `CWMONTHLY` and drop the code from the structure type |
| C-33 | Open | Applies later (planned design), spec decision: specs have rules `TOTAL_LOON` … `NET` but no rules coded `BASIC` and `GROSS`, so the payslip's `basic_wage` and `gross_wage` would show 0 | Not decided | | Add rules with codes `BASIC` and `GROSS`, or rename existing rules to those codes |
| C-36 | Open | Applies later (planned design), spec decision: listing data files in `_get_data_files_to_update` lets the daily cron re-load them, which conflicts with append-only rate data (AD-5) | Not decided; decide together with C-23 | | List the payroll data files in `_get_data_files_to_update`, after making sure a reload cannot overwrite or delete dated rate records |
| C-82 | Open | Applies later (planned design), spec decision: planned new models are named `hr.tax.bracket`, `hr.svb.parameters`, `hr.loonbelasting.tabel`, `hr.wage.*` and `hr.employee.bijzonder.tarief`, not `l10n_cw.*` | Not decided | | Rename the planned models to `l10n_cw.*` before they are built |
| C-83 | Open | Applies later (planned design), spec decision: the planned `singleton` field on `hr.salary.rule` has no `l10n_cw_` prefix (existing `l10n_cw_*` fields conform) | Not decided | | Name the field `l10n_cw_singleton` |

# Open decisions

- **C-33, rule codes `BASIC` and `GROSS`:** this one has a functional impact. Core fills the payslip's `basic_wage` and `gross_wage` from rules with these codes, so without them both fields show 0 on every payslip and in payroll reporting. Decide before Epic 2 salary rules are built.
- **C-12, separate accounting module:** all 25 peers keep accounting in a `l10n_<cc>_hr_payroll_account` bridge. Splitting needs a Curaçao chart-of-accounts module to depend on, and we could not confirm that one exists. Also settles the `hr_payroll_account` part of C-06.
- **C-06, depends:** whether `hr_attendance` is needed, and dropping the redundant `hr` and `hr_holidays`.
- **C-53, `noupdate` on record rules:** deferred in the Story 1.3 review; decide before production.
- **C-23 and C-36, data reload:** how peer-style data reloading fits the append-only rate design (AD-5).
- **C-32, structure code:** whether `CWMONTHLY` moves from the structure type to the structure.
- **C-82, model names:** whether planned new models get the `l10n_cw.` prefix.
- **C-83, `singleton` field:** whether it gets the `l10n_cw_` prefix.

# Maintaining this register

- When an Open divergence is decided, change its Status to `Decided` and fill in the reason, who decided and the date.
- When the module is aligned with the checklist, delete the row (git history keeps it) and note the alignment in the story's change log.
- When the script reports a new divergence, add a row for it in the same change that introduced it, as `Open` unless it was decided in that change.
