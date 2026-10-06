::: {custom-style="Title"}
l10n_cw_hr_payroll
:::
::: {custom-style="Subtitle"}
Official Odoo Payroll Localization Checklist
:::

This checklist lists the conventions that the 25 payroll localizations shipped with Odoo 19 Enterprise (the `l10n_<cc>_hr_payroll` modules) follow. Odoo publishes no formal list of rules for a payroll localization, so these are de-facto conventions: they were derived by reading the shipped modules and counting how many of them follow each pattern. Baseline: Odoo 19.0 Enterprise. Derived 2026-10-06.

We keep to these conventions where we can so that the official-localization track stays open: if Curaçao payroll is ever offered to Odoo as an official localization, the module should already look like its peers. The manifest category `Human Resources/Payroll` (decided 2026-07-07) was the first decision taken for this reason.

How the checklist is used:

- `tools/check_l10n_conformance.py` checks the mechanical items (column "Checked by script") automatically before every commit, through the git pre-commit hook. It only prints warnings and never blocks a commit.
- Items the script cannot check, or checks only partially, are reviewed by hand at each story's code review.
- Every place where the module knowingly differs from this checklist is recorded in [official-localization-divergences.md](official-localization-divergences.md). The script uses that register to tell known divergences from new ones.

How to read the tables:

- **Peers** is how many of the 25 shipped payroll modules follow the convention. The 25 matching `l10n_<cc>_hr_payroll_account` accounting modules ("bridges") are counted separately where they matter. `l10n_fr_hr_payroll` is a legacy outlier (not authored by Odoo, French source strings) and explains many "24/25" counts.
- **Checked by script** is Yes, Partial (a heuristic; a human confirms the result), Not yet (checkable, but the script gets the check when the artifact it inspects is added), No (manual) or No.
- **Applies** is "Now" when the module already contains the artifact the check looks at, or "Later" with the story or epic that will introduce it.

# Manifest (C-0x)

| ID | Convention | Peers | Checked by script | Applies |
|---|---|---|---|---|
| C-01 | Technical name is `l10n_<cc>_hr_payroll` | 25/25 | Yes | Now |
| C-02 | Display name is `<Country> - Payroll` (for us: `Curaçao - Payroll`) | 23/25 | Yes | Now |
| C-03 | `category` is `Human Resources/Payroll` | 25/25 | Yes | Now |
| C-04 | `countries` is `['<cc>']` (for us: `['cw']`) | 25/25 | Yes | Now |
| C-05 | `license` is `OEEL-1` | 25/25 | Yes | Now |
| C-06 | `depends` includes `hr_payroll` and never `hr_payroll_account`, `hr`, `hr_holidays` or `hr_attendance`; usually also `hr_payroll_holidays` (17) and `hr_work_entry_holidays` (16) | 25/25 include `hr_payroll`; 0/25 list a forbidden one | Yes | Now |
| C-07 | Module auto-installs (`auto_install` is `['hr_payroll']` in 22, `True` in 2) | 24/25 | Yes | Now |
| C-08 | `version` is `'1.0'` or absent; author Odoo S.A.; no `website`, `summary`, `installable` or `application` keys; `description` present | version `'1.0'` 14, absent 11; extra keys 0/25; description 24/25 | Yes | Now |
| C-09 | No `post_init_hook`, `pre_init_hook` or `uninstall_hook` | 25/25 | Yes | Now |

# Layout and files (C-1x)

| ID | Convention | Peers | Checked by script | Applies |
|---|---|---|---|---|
| C-10 | Folders: `data/` and `models/` always, `views/` 24, `i18n/` 23, `tests/` 19; `security/` (9) only when the module adds new models; `report/` 8, `wizard(s)/` 9 | as listed | Yes | Now |
| C-11 | One Python file per inherited model, named after it (`hr_version.py`, `hr_payslip.py`, `hr_payroll_structure_type.py`, `hr_employee.py`) | at least 21/25 | Yes | Later — Story 1.4 and on |
| C-12 | Accounting lives in a separate, auto-installing `l10n_<cc>_hr_payroll_account` bridge module, which depends on `hr_payroll_account`, the country's chart-of-accounts module and the payroll module, and holds the chart-template data and rule accounts | 25/25 countries have a bridge; 0/25 base modules depend on `hr_payroll_account` | Yes (via C-06) | Now |
| C-13 | View file names: `hr_employee_views.xml` 23, `hr_contract_template_views.xml` 19, `report_payslip_templates.xml` 15, `hr_payroll_report.xml` 13 | as listed | Not yet | Later — views |
| C-14 | Payslip report action `action_report_payslip_<cc>` whose `report_name` contains `l10n_<cc>`, set as the structure's `report_id`. Core only offers reports whose `report_name` contains `l10n_` plus the country code (`hr_payroll/models/hr_payroll_structure.py:22-38`) | 17/25 (action name), 16/25 (set on structure) | Yes | Later — payslip report |

# Data and XML ids (C-2x)

| ID | Convention | Peers | Checked by script | Applies |
|---|---|---|---|---|
| C-20 | Data file names: `hr_salary_rule_category_data.xml` 24, `hr_payroll_structure_type_data.xml` 24, `hr_payroll_structure_data.xml` 24, `hr_salary_rule*_data.xml` 22, `hr_rule_parameters_data.xml` 13 (or `hr_rule_parameter_data.xml` 9), `hr_payslip_input_type_data.xml` 17, `resource_calendar_data.xml` 9 | 22-24/25 for the main files | Yes | Later — Epic 1 and Epic 2 data |
| C-21 | Order in manifest `data`: categories, structure type, report action, structure, rule parameters, input types, rules, views (security position varies) | 4/4 sampled | Yes | Later — data files |
| C-22 | Demo file `data/l10n_<cc>_hr_payroll_demo.xml` under the manifest `demo` key | 24/25 | Not yet | Later — optional demo data |
| C-23 | No `noupdate` on salary rules, categories or parameters; `noupdate` only for calendars, sequences, crons, warnings, demo data and record rules | 0/25 put `noupdate` on payroll logic | Yes | Later — salary-rule and rate data |
| C-24 | XML ids `structure_type_employee_<cc>`, `hr_payroll_structure_<cc>_employee_salary`, `<module>_<structure>_basic_salary_rule` | 17, 15 and 23 of 25 | Yes | Later — structure and rule data |
| C-25 | Country-specific UI hidden with `invisible="country_code != 'XX'"`; country-specific Python gated on `company.country_code` | 23/25 (views), 22/25 (Python) | Not yet | Later — views and models |

# Salary structures and rules (C-3x)

| ID | Convention | Peers | Checked by script | Applies |
|---|---|---|---|---|
| C-30 | Structure type has `country_id = base.<cc>` and is named `<Country>: Employee` | 25/25 (country), 17/25 (name) | Yes | Later — structure data |
| C-31 | Structure has `country_id`, `type_id` and `rule_ids eval="[]"` (without it, core copies its default rules into the structure); the structure type points back through `default_struct_id` | 25/25, 24/25 (back-pointer) | Yes | Later — structure data |
| C-32 | The code `<CC>MONTHLY` sits on the structure; the structure type has no code field | 15/25 | Yes | Later — structure data |
| C-33 | Rules with codes `BASIC`, `GROSS` and `NET` exist, because core reads them: `hr_payroll/models/hr_payslip.py:433-450` fills the payslip's `basic_wage`, `gross_wage` and `net_wage` from them, and lines 349 and 598 use `NET` to detect a negative net | 24 (BASIC), 24 (GROSS), 25 (NET) of 25 | Yes | Later — Epic 2 salary rules |
| C-34 | Reuse the core categories `hr_payroll.BASIC`, `ALW`, `DED`, `NET` (25/25) and `GROSS` (24/25); add own extra categories in a category file | 24/25 ship a category file | Not yet | Later — Epic 2 salary rules |
| C-35 | Every rule has `struct_id` and `sequence`; rule codes are uppercase | 1499/1499 rules | Yes | Later — Epic 2 salary rules |
| C-36 | `hr.payslip._get_data_files_to_update` lists the payroll data files, so the daily cron `ir_cron_update_payroll_data` re-loads them | 18/25 | Yes | Later — salary-rule and rate data |
| C-37 | `hr.payroll.structure.type._get_selection_schedule_pay` limits the offered pay periods | 21/25 | Not yet | Later — structure type model |
| C-38 | `hr.version._get_whitelist_fields_from_template` adds the `l10n_<cc>_` contract fields, with a contract template view | 19/25 | Not yet | Later — Story 1.9 |

# Rates (C-4x)

| ID | Convention | Peers | Checked by script | Applies |
|---|---|---|---|---|
| C-40 | Statutory rates are `hr.rule.parameter` records with dated `.value` records, read through `payslip._rule_parameter()` | 23/25 | Yes | Later — rate data |
| C-41 | Parameter codes are `l10n_<cc>_*` and carry `country_id` | 557/557 parameters | Not yet | Only if C-40 is adopted |
| C-42 | Where a peer uses its own statutory-rate model, the model name is prefixed (`l10n.ch.*.rate`, `l10n.mx.hr.infonavit`) | 2/25 | Yes (via C-82) | Later — rate models |

# Security (C-5x)

| ID | Convention | Peers | Checked by script | Applies |
|---|---|---|---|---|
| C-50 | No own `res.groups` or privileges; the module uses the `hr_payroll` groups | 0/25 define groups | Yes | Now |
| C-51 | Access rows use the `hr_payroll` groups and cover only the module's own new models, never core payroll models | 8/9 and 9/9 of the modules with a `security/` folder | Yes | Now |
| C-52 | Record rules only for multi-company (`[('company_id','in',company_ids)]`) on the module's own models | 5/25 have record rules | Yes | Now |
| C-53 | Record-rule files are `noupdate="1"` | 5/5 | Yes | Now |
| C-54 | Every new model has an access row | 9/9 | Yes | Later — first new model |

# Translations (C-6x)

| ID | Convention | Peers | Checked by script | Applies |
|---|---|---|---|---|
| C-60 | Source strings are in English | 24/25 | No (manual) | Now |
| C-61 | `i18n/<module>.pot` exists | 23/25 | Yes | Now |
| C-62 | One `.po` file per local language, with header `Odoo Server 19.0+e` | 23/25 | Yes | Now |

# Tests (C-7x)

| ID | Convention | Peers | Checked by script | Applies |
|---|---|---|---|---|
| C-70 | Tests live in the base module | 19/25 | Yes | Now |
| C-71 | Every test class is tagged `('post_install_l10n', 'post_install', '-at_install')` | 19/19 | Yes | Now |
| C-72 | Salary-value tests use `TestPayslipValidationCommon`, `setup_country('<cc>')` and `_validate_payslip({code: value})`, which compares to the cent | 20/25 bridges | Not yet | Later — Epic 2 |
| C-73 | `test_contract_template_whitelist.py` exists when contract fields are added | 19/19 | Not yet | Later — Story 1.9 |

# Code style (C-8x)

| ID | Convention | Peers | Checked by script | Applies |
|---|---|---|---|---|
| C-80 | File header `# Part of Odoo. See LICENSE…` | 397/452 files | No | Not applicable — it states Odoo's copyright |
| C-81 | No `# -*- coding: utf-8 -*-` line | 412/452 files omit it | Yes | Now |
| C-82 | New models are named `l10n_<cc>.*` | 108/120 non-report models | Yes | Later — first new model |
| C-83 | Fields added to core models are prefixed `l10n_<cc>_` | 21/23 modules | Yes | Later — fields on core models |

# Maintaining this checklist

- Re-derive the checklist from the shipped modules at every Odoo major upgrade, alongside the [upgrade watch list](upgrade-watch-list.md): recount the peers, and add, change or retire conventions that moved.
- When a new convention is found, add a check here in the same change, and teach the script to check it if it is mechanical.
- IDs are stable references, used by the script and the divergence register. Append new IDs within their group; never renumber or reuse an existing one.
