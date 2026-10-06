::: {custom-style="Title"}
l10n_cw_hr_payroll
:::
::: {custom-style="Subtitle"}
Upgrade Watch List — Native Odoo Dependencies
:::

This document lists every Odoo native module and framework feature that `l10n_cw_hr_payroll` directly hooks into, and which specific groups, fields, rules, methods or behaviours would require a review if Odoo changes them in a future major release. Baseline: Odoo 19.0 Enterprise (build `19.0-20260528`).

Use this list as a checklist at the start of every Odoo major-version upgrade. Every story that adds a new hook into Odoo (an inherited model, an overridden method, a referenced XML id, a relied-on behaviour) adds an entry in the same change. Section numbers are stable references: append new entries, never renumber existing ones.

**Legend — Impact column:**

- 🔴 **High** — change here will break functionality silently or raise an error at runtime
- 🟠 **Medium** — change here causes degraded behaviour or a visible error; fixable with moderate effort
- 🟡 **Low** — change here causes a cosmetic or minor regression; quick fix

Line numbers refer to the Odoo 19 Enterprise source and are a starting point for the diff, not a guarantee.

# 1. `hr_payroll` — Payroll

## 1.1 `hr_payroll.group_hr_payroll_user` / `group_hr_payroll_manager` — implied core groups

| Detail | Value |
|---|---|
| Our file | `security/hr_payroll_security.xml` |
| Impact | 🔴 High |

Our Gebruiker role implies `hr_payroll.group_hr_payroll_user` and our Manager role implies `hr_payroll.group_hr_payroll_manager`, because every core payroll access right (`hr.payslip`, `hr.payslip.line`, `hr.payslip.run`, …) is bound to those two groups. In 19 they in turn imply `hr.group_hr_user` and `hr.group_hr_manager` (`hr_payroll/security/hr_payroll_security.xml:11-25`), which gives our roles HR employee rights (PO-accepted scope, 2026-10-06). If Odoo renames these groups, the install fails on the unknown XML id; if it changes what they imply, our roles silently gain or lose HR rights.

**Review:** Diff `hr_payroll/security/hr_payroll_security.xml` between versions. Confirm both XML ids still exist, still carry the payroll ACLs, and still imply the same `hr` groups. Rerun `tests/test_security.py::test_manager_ladders_to_user_and_core_payroll_groups` and `test_payroll_user_reads_and_edits_all_payslips`. If the implied `hr` groups changed, update PRD "Users and Roles".

## 1.2 Core record rules on `hr.payslip`

| Detail | Value |
|---|---|
| Our file | `security/hr_payroll_security.xml` (`rule_payslip_employee_own`, `rule_payslip_accountant_all`) |
| Impact | 🔴 High |

We rely on `hr_payroll_rule_officer` and `hr_payslip_rule_manager` (both `[(1,'=',1)]`, lines 37-48) to give Gebruiker and Manager all payslips. Our own rules sit beside them, and the global `ir_rule_hr_payslip_multi_company` (`[('company_id', 'in', company_ids)]`, line 75) is ANDed on top of everything. Odoo ORs the group rules of a user's groups, which is why the Accountant carries its own all-payslips rule. If the officer rule is ever narrowed (its name, "Officer and subordinates Payslip", hints at that), Gebruiker silently stops seeing all payslips.

**Review:** Confirm the officer and manager rules still use `[(1,'=',1)]` and the multi-company rule is unchanged. Rerun all of `tests/test_security.py`.

## 1.3 `hr.payslip.state` selection values

| Detail | Value |
|---|---|
| Our file | `security/hr_payroll_security.xml` (`rule_payslip_employee_own`), `tests/test_security.py` |
| Impact | 🔴 High |

The own-payslip rule shows employees only `state in ('validated', 'paid')`. The 19 selection is `draft` / `validated` / `paid` / `cancel` (`hr_payroll/models/hr_payslip.py:67-71`); older versions used `done`. If a state is renamed or a new final state is added, the rule silently hides all, or some, payslips from employees, with no error anywhere.

**Review:** Diff the `state` selection on `hr.payslip`. If the final states changed, update the rule domain and the PRD §Security XML together. Rerun `test_employee_sees_only_own_final_payslips` and `test_employee_cannot_read_own_draft_payslip`.

## 1.4 `hr.payslip.done_date` and the `has_wrong_data` compute

| Detail | Value |
|---|---|
| Our file | `tests/test_security.py` (`setUpClass`) |
| Impact | 🟡 Low |

Our test fixture validates payslips by writing `state` and `done_date` directly, mirroring `action_payslip_done` (`hr_payroll/models/hr_payslip.py:588-596`). `_compute_is_wrong_version` (lines 399-404) compares `version_id.last_modified_date > done_date` for validated and paid slips and crashes when `done_date` is empty (hit on 2026-10-06). If validation gains other required side effects, the fixture no longer matches real behaviour.

**Review:** Diff `action_payslip_done` and `_compute_is_wrong_version`. Make the fixture write every field validation now sets.

## 1.5 `/print/payslips` controller — payroll-user check

| Detail | Value |
|---|---|
| Our file | none yet (Stories 3.6 and 4.1) |
| Impact | 🟠 Medium |

`hr_payroll/controllers/main.py:16-19` returns not-found unless the user has `hr_payroll.group_hr_payroll_user`. Our Medewerker and Accountant roles do not, so the standard print route cannot serve them; Stories 3.6/4.1 must provide their own download path. If Odoo loosens this check, employees might reach bulk printing without our own-payslip rule in front; if it moves or renames the route, our future download path must follow.

**Review:** Diff `hr_payroll/controllers/main.py`. Re-check whichever download path Stories 3.6/4.1 built against the new route and its access check.

## 1.6 Core access rows for payslip child models

| Detail | Value |
|---|---|
| Our file | `security/ir.model.access.csv` |
| Impact | 🟠 Medium |

Core grants `hr.payslip`, `hr.payslip.line`, `hr.payslip.input`, `hr.payslip.worked_days` and `hr.payslip.run` only to `hr_payroll.group_hr_payroll_user` (`hr_payroll/security/ir.model.access.csv:7-13`). Our CSV adds read on `hr.payslip` for Medewerker and Accountant and on `hr.payslip.run` for Accountant. Child-model access for these roles is deferred to Stories 3.6/4.1. If Odoo regroups these rows or adds child models that a payslip form reads, our roles hit AccessError on screens they can open.

**Review:** Diff the core CSV. List the models a payslip form and report now read, and confirm our roles have matching rows plus own-record rules for Medewerker.

## 1.7 Model XML ids `hr_payroll.model_hr_payslip` / `model_hr_payslip_run`

| Detail | Value |
|---|---|
| Our files | `security/hr_payroll_security.xml`, `security/ir.model.access.csv` |
| Impact | 🔴 High |

Our rules and access rows reference the models through the `hr_payroll.` prefix (`hr_payroll/models/hr_payslip.py:33`, `hr_payslip_run.py:23`). If either model moves to another module (for example `hr_work_entry_enterprise`), our module fails to install or upgrade.

**Review:** Confirm both models are still defined in `hr_payroll`; otherwise change the prefix in the XML and CSV.

## 1.8 Payroll root menu `hr_work_entry_enterprise.menu_hr_payroll_root`

| Detail | Value |
|---|---|
| Our file | none yet (future menus) |
| Impact | 🟡 Low |

The Payroll root menu is defined in `hr_work_entry_enterprise/views/hr_payroll_menu.xml:6-11` (not in `hr_payroll`) with `hr.group_hr_manager`; `hr_payroll/views/hr_payroll_menu.xml:3-5` adds `group_hr_payroll_user`. Menus we add under it must use the `hr_work_entry_enterprise.` XML id, and they stay invisible to Medewerker and Accountant unless we give those roles their own entry point.

**Review:** Confirm the menu's XML id and module before referencing it in a new view story.

# 2. `hr` — Employees and Versions

## 2.1 `hr.version` replaces `hr.contract`; salary-rule variable `version`

| Detail | Value |
|---|---|
| Our files | `__manifest__.py` (no `hr_contract` in `depends`), `tests/test_security.py`, all future salary rules |
| Impact | 🔴 High |

Odoo 19 removed `hr_contract` and folded contracts into `hr.version` (decided 2026-07-07, review D1). Payslips carry `version_id` (`hr_payroll/models/hr_payslip.py:114`), and the salary-rule context exposes `version` (line 1061). Our tests create employees with `date_version`, `contract_date_start` and `wage`, and every future salary rule reads contract data from `version`. Note: `contract_date_start` and `wage` are restricted to `hr_payroll.group_hr_payroll_user` (`hr_payroll/models/hr_version.py:23-28`), so code running as Medewerker or Accountant cannot read them. This model is new in 19, so field names and the rule context may still move.

**Review:** Diff `hr.version` and the salary-rule localdict (`_get_localdict` or its successor). Grep our rules and tests for every `version.` field and confirm it still exists with the same meaning and access group.

# 3. `account` / `accountant` — Accounting

## 3.1 `account.group_account_readonly`

| Detail | Value |
|---|---|
| Our file | `security/hr_payroll_security.xml` (`group_l10n_cw_accountant`) |
| Impact | 🟠 Medium |

Our Accountant role implies `account.group_account_readonly` to read the journal entries payroll runs post. In 19, `accountant` renames it "Read-only" under the accounting privilege (`accountant/security/accounting_security.xml:19-24`), and `hr_payroll_account` uses it only to show the journal-entry smart buttons on payslips and runs. If it is renamed or its ACLs change, the Accountant loses journal read access.

**Review:** Confirm the XML id still exists and still grants read on `account.move`. Rerun `test_accountant_reads_journal_entries`.

# 4. `base` — Security and Module Framework

## 4.1 `res.groups.privilege` and `res.groups.privilege_id`

| Detail | Value |
|---|---|
| Our file | `security/hr_payroll_security.xml` |
| Impact | 🔴 High |

Odoo 19 groups roles under a `res.groups.privilege` (with `category_id`, here `base.module_category_human_resources`) instead of an `ir.module.category`; `hr_payroll` uses the same pattern (`hr_payroll/security/hr_payroll_security.xml:5-9`). On the user form our four roles render as one "Salarisadministratie Curaçao" dropdown (verified 2026-10-06), yet the ORM still allows two roles from one privilege on a user (our Accountant+Medewerker test passes). The model is new in 19, so its fields or rendering may change.

**Review:** Confirm `res.groups.privilege` and `privilege_id` still exist and `base.module_category_human_resources` is still valid. Open a user form and check the role field still shows all four roles.

## 4.2 `res.users.group_ids` (was `groups_id`)

| Detail | Value |
|---|---|
| Our file | `tests/test_security.py` |
| Impact | 🟡 Low |

Renamed in 19. Our tests extend a user's groups through `group_ids`.

**Review:** Confirm the field name; update the tests if it changed.

## 4.3 `Model.has_access()` / `check_access()`

| Detail | Value |
|---|---|
| Our file | `tests/test_security.py` (`test_accountant_reads_journal_entries`) |
| Impact | 🟡 Low |

Introduced in 18, replacing `check_access_rights()` / `check_access_rule()`, which no Enterprise 19 code calls any more. Never use the old names in new code.

**Review:** Confirm `has_access` still exists with the same signature.

## 4.4 `Command` inside XML `eval`

| Detail | Value |
|---|---|
| Our file | `security/hr_payroll_security.xml` |
| Impact | 🟡 Low |

We write x2many values as `eval="[Command.link(ref(...))]"`, as `voip` and `room` do in 19 (`hr_payroll` itself still uses the older `(4, ref(...))` tuples). If `Command` ever leaves the XML eval context, the install fails at load time.

**Review:** Confirm Enterprise still uses `Command` in XML `eval`.

## 4.5 Manifest key `countries`

| Detail | Value |
|---|---|
| Our file | `__manifest__.py` (`'countries': ['cw']`) |
| Impact | 🟡 Low |

Since 17, Apps hides or ranks down modules whose countries do not match a company's country, so our module only appears when a company's country is Curaçao.

**Review:** Confirm the key and its Apps behaviour, and that `cw` is still in `res.country`.

# 5. Odoo 19 Platform Constraints (Recorded)

Behaviour of the platform or of this deployment that is not a hook in our code, but that shapes how we build, test or deploy.

## 5.1 `http_interface` default changes to `127.0.0.1` in 20.0

**What it is:** every Odoo 19 run logs "missing --http-interface/http_interface, using 0.0.0.0 by default, will change to 127.0.0.1 in 20.0". The Coolify `odoo.conf` sets no `http_interface`.

**What breaks:** on Odoo 20, Odoo would listen only on the container's loopback, so Coolify's proxy and Docker port mapping can no longer reach it: the instance becomes unreachable (502), including the websocket port.

**Rule to follow:** before upgrading, set `http_interface = 0.0.0.0` in the Coolify `odoo.conf` (this also silences the warning on 19).

**Status (2026-10-06):** not applied yet; to be done by the system administrator any time before moving to Odoo 20. It is safe on Odoo 19, because `0.0.0.0` is today's default: nothing changes except that the warning disappears. The config file needs `sudo`, so it cannot be changed from the development environment. Steps on the Coolify host:

1. Back up the config file:

   ```bash
   sudo cp /data/coolify/services/bydogoqbgp8c4v7xhx71x0rq/config/odoo.conf{,.bak2}
   ```

2. Add the setting under the real `[options]` line (no-op if it is already there):

   ```bash
   sudo grep -q '^http_interface' /data/coolify/services/bydogoqbgp8c4v7xhx71x0rq/config/odoo.conf \
     || sudo sed -i '/^\[options\]/a http_interface = 0.0.0.0' /data/coolify/services/bydogoqbgp8c4v7xhx71x0rq/config/odoo.conf
   ```

3. Check it: `sudo grep -n -A2 '^\[options\]' /data/coolify/services/bydogoqbgp8c4v7xhx71x0rq/config/odoo.conf` must show `http_interface = 0.0.0.0` on the next line.

4. Restart Odoo:

   ```bash
   sudo docker restart $(sudo docker ps -q --filter ancestor=odoo:19.0 --filter name=bydogoqbgp8c4v7xhx71x0rq)
   ```

The next Odoo run no longer logs `missing --http-interface/http_interface`. To undo, restore the backup with `sudo mv …/odoo.conf{.bak2,}` and restart. When applied, replace this status line with the date it was done.

## 5.2 `-u … --test-enable` rolled back the upgrade on this build

**What it is:** on the Coolify instance (`odoo:19.0`, build `19.0-20260528`), `-u l10n_cw_hr_payroll --test-enable --stop-after-init` finished with all tests passed, yet the module had no XML ids afterwards; the same command without `--test-enable` saved them (observed 2026-10-05). The cause is not confirmed from source (Odoo's loading and test code is not on the dev machine).

**What breaks:** new groups, rules, views or data look installed in the test run but never reach the database or the web UI.

**Rule to follow:** upgrade first without `--test-enable`, then run the tests as a separate step (`docs/guides/testing.md`). Re-test this behaviour on every new build.

## 5.3 `@route(type='json')` deprecated in favour of `type='jsonrpc'`

**What it is:** since 19, `type='json'` is a deprecated alias (warning seen in the logs from another module); Enterprise 19 has no `type='json'` routes left.

**What breaks:** the alias may be removed in 20; any controller using it would stop responding.

**Rule to follow:** future controllers in this module use `type='jsonrpc'` (or `'http'`). The module has no controllers yet.

## 5.4 Dark mode and Bootstrap variables (theming, not in use)

**What it is:** Odoo 19 has no `.o_dark_mode` class; dark mode loads the separate `web.assets_web_dark` bundle (`*.dark.scss` files). Bootstrap button variables carry no `bs-` prefix (`--btn-bg`, …).

**What breaks:** nothing today. The module ships no stylesheet (AD-15, decided 2026-10-05).

**Rule to follow:** if theming ever returns, register dark values in `web.assets_web_dark` and use `--#{$prefix}btn-*` so the variables follow whatever prefix Odoo uses.

## 5.5 Translation export moved to the `odoo i18n` subcommand

**What it is:** Odoo 19 has no `--i18n-export` server option any more (`error: no such option: --i18n-export`, seen 2026-10-06). Exporting is now `odoo i18n export [-c CONFIG] [-d DB] [-l LANG …] [-o FILE] MODULE …`; the default language is `pot` (the template), and without `-o` it writes into each module's `i18n/` folder. Loading a language is `odoo i18n loadlang -l <code>`.

**What breaks:** older instructions and scripts that call `--i18n-export` / `--i18n-import` fail immediately.

**Rule to follow:** regenerate the template with `odoo i18n export -c <odoo.conf> -d <db> -o l10n_cw_hr_payroll.pot l10n_cw_hr_payroll` (the file is generated by Odoo, so it is never edited by hand; first exported this way on 2026-10-06). Re-check the subcommand's `--help` on every major upgrade.

# Summary — Priority Order for Upgrade Review

| Priority | Native module | Specific touch-point | Risk |
|---|---|---|---|
| 1 | `hr_payroll` | Payroll groups and their implied `hr` groups (§1.1) | 🔴 High |
| 2 | `hr_payroll` | Officer/manager/multi-company record rules on `hr.payslip` (§1.2) | 🔴 High |
| 3 | `hr_payroll` | `hr.payslip.state` values in the own-payslip rule (§1.3) | 🔴 High |
| 4 | `hr_payroll` | `model_hr_payslip` / `model_hr_payslip_run` XML ids (§1.7) | 🔴 High |
| 5 | `hr` | `hr.version` fields and salary-rule `version` context (§2.1) | 🔴 High |
| 6 | `base` | `res.groups.privilege` / `privilege_id` (§4.1) | 🔴 High |
| 7 | platform | `http_interface` default on Odoo 20 (§5.1) | 🔴 High |
| 8 | `hr_payroll` | `/print/payslips` payroll-user check (§1.5) | 🟠 Medium |
| 9 | `hr_payroll` | Core access rows for payslip child models (§1.6) | 🟠 Medium |
| 10 | `account` | `account.group_account_readonly` (§3.1) | 🟠 Medium |
| 11 | platform | `--test-enable` rollback on upgrade (§5.2) | 🟠 Medium |
| 12 | `hr_payroll` | `done_date` / `has_wrong_data` in the test fixture (§1.4) | 🟡 Low |
| 13 | `hr_payroll` | Payroll root menu XML id (§1.8) | 🟡 Low |
| 14 | `base` | `res.users.group_ids` (§4.2) | 🟡 Low |
| 15 | `base` | `has_access()` / `check_access()` (§4.3) | 🟡 Low |
| 16 | `base` | `Command` in XML `eval` (§4.4) | 🟡 Low |
| 17 | `base` | Manifest `countries` (§4.5) | 🟡 Low |
| 18 | platform | `@route(type='json')` alias (§5.3) | 🟡 Low |
| 19 | platform | Dark-mode bundle and Bootstrap variables (§5.4) | 🟡 Low |
| 20 | platform | Translation export via `odoo i18n export` (§5.5) | 🟡 Low |
