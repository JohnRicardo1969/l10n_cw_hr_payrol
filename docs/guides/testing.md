::: {custom-style="Title"}
l10n_cw_hr_payroll
:::
::: {custom-style="Subtitle"}
Testing Guide — running the module's automated tests on Odoo 19
:::

# Purpose

The module ships automated tests in `l10n_cw_hr_payroll/tests/`. They prove that the module behaves as specified on a real Odoo 19 Enterprise database, instead of relying on someone clicking through screens. Run them:

- after every change to the module, before committing;
- after pulling a new version onto a server, before users work with it;
- whenever something behaves unexpectedly, to see whether a known rule broke.

What the tests cover today:

| Test file | What it proves |
|---|---|
| `tests/test_security.py` | The four roles and the own-payslip rule (FR026, FR027): an employee sees only their own final payslips (not drafts, not anyone else's) and cannot edit, create or delete payslips; the employee role is for internal users only; a user without a payroll role has no payslip access; the Accountant reads all payslips and runs but cannot change them, can read journal entries, and keeps full read access when also given the employee role; the Payroll User reads and edits all payslips; the Manager reads all payslips and includes the Payroll User role and Odoo's payroll groups. |

Later stories add their own test files (rate lookups, salary rules, run close). The statutory calculations must reconcile to the official 2026 publications within XCG 0.02, and those checks will live here too.

# The commands

Upgrading and testing are two separate steps. On this Odoo 19 build, a run with `--test-enable` rolls the whole upgrade back when it finishes (observed 2026-10-05: all tests passed, yet none of the module's records were saved). The test run therefore checks the code, but never updates the database.

## Step 1: upgrade the module

Run this whenever the module's code changed, so the database matches it:

```bash
sudo docker exec $(sudo docker ps -q --filter ancestor=odoo:19.0 --filter name=bydogoqbgp8c4v7xhx71x0rq) \
  odoo -c /etc/odoo/odoo.conf -d caribware_dev_19_01 -u l10n_cw_hr_payroll --stop-after-init --http-port=8099
```

## Step 2: run the tests

On the Coolify server, with the Odoo container running:

```bash
sudo docker exec $(sudo docker ps -q --filter ancestor=odoo:19.0 --filter name=bydogoqbgp8c4v7xhx71x0rq) \
  odoo -c /etc/odoo/odoo.conf -d caribware_dev_19_01 -u l10n_cw_hr_payroll --test-enable --stop-after-init --http-port=8099
```

What each part does:

| Part | Meaning |
|---|---|
| `sudo docker exec <container>` | Runs a command inside the Odoo container that is already running. |
| `$(sudo docker ps -q --filter ancestor=odoo:19.0 --filter name=bydogoqbgp8c4v7xhx71x0rq)` | Finds that container's ID: the one built from the `odoo:19.0` image whose name contains the Coolify service ID. |
| `odoo` | Starts a second, temporary Odoo process next to the running one. |
| `-c /etc/odoo/odoo.conf` | Uses the same configuration file as the live server (database host, user, addons paths). |
| `-d caribware_dev_19_01` | The database to test against. |
| `-u l10n_cw_hr_payroll` | Loads the module's current code and selects which module's tests run. Combined with `--test-enable`, the upgrade is rolled back at the end, so Step 1 is still needed. |
| `--test-enable` | Turns the test runner on. Without it, `-u` only upgrades (and keeps the upgrade). |
| `--stop-after-init` | Exits when the upgrade and tests are finished, instead of staying up as a web server. |
| `--http-port=8099` | Gives the temporary process its own port. The live server already holds port 8069; without this flag the command stops with "Port 8069 is in use by another program". |

Use a development or test database, never production. Test records (users, employees, payslips) and the upgrade done during the test run are rolled back afterwards.

After Step 1, if the change also touched Python code, restart the container so the running server loads it:

```bash
sudo docker restart $(sudo docker ps -q --filter ancestor=odoo:19.0 --filter name=bydogoqbgp8c4v7xhx71x0rq)
```

# Reading the result

The line that matters is near the end:

```
odoo.tests.result: 0 failed, 0 error(s) of 13 tests when loading database 'caribware_dev_19_01'
```

- `0 failed, 0 error(s)` means every test passed. The test count grows as stories add tests.
- `failed` means a test ran and its check did not hold: the behaviour is wrong (or the test is). The lines above it show which test and why.
- `error(s)` means a test crashed before it could check anything, for example on a missing field or a broken data file. Read the traceback above it.

Lines that look alarming but are expected:

- `Access Denied by ACLs …` and `Access Denied by record rules …` at INFO level: the security tests deliberately try forbidden actions and confirm Odoo blocks them.
- `Signup email sent for user <cw_…>`: Odoo inviting the temporary test users. The rollback discards these emails.
- Warnings from other modules (for example `cw_prepaid_topup` deprecation warnings) are unrelated to this module.

If `test_user_without_cw_group_has_no_payslip_access` is the only failure, another installed module grants every internal user read access to payslips. That is a data leak to investigate, not a test to relax.

# Conformance check before each commit

`tools/check_l10n_conformance.py` compares the module with the conventions of the official Odoo payroll localizations ([checklist](../reference/official-localization-checklist.md)). It needs no Odoo: it only reads the module's files.

It runs automatically before every `git commit` through the hook `tools/git-hooks/pre-commit`, after this one-time setup in each clone of the repository:

```bash
git config core.hooksPath tools/git-hooks
```

Run it by hand from the repository root:

```bash
python3 tools/check_l10n_conformance.py            # summary, new and open divergences
python3 tools/check_l10n_conformance.py --verbose  # every check with its status
```

It only warns and always exits 0, so it never blocks a commit (`--strict` makes it exit 1 when there is a new divergence). Reading the result:

- `WARNING NEW C-xx` is a new divergence. Either fix it, or record it in the [divergence register](../reference/official-localization-divergences.md) in the same change.
- `open C-xx` is a known divergence that still needs a decision.
- "N known divergences decided" counts the divergences that were deliberately kept.
- `STALE C-xx` means a registered divergence now conforms: remove its row from the register.

# Running on a local Odoo

On a development machine with Odoo 19 Enterprise sources, the same run is:

```bash
odoo-bin -d <test-db> \
  --addons-path=<community>/addons,<enterprise-19.0>,<path-to-this-repo> \
  -u l10n_cw_hr_payroll --test-enable --stop-after-init
```

Add `--test-tags /l10n_cw_hr_payroll` to be sure only this module's tests run, or `--test-tags /l10n_cw_hr_payroll:TestPayrollSecurity` to run a single test class.

# Adding tests

- Put each test file in `l10n_cw_hr_payroll/tests/`, named `test_<topic>.py`, and import it in `tests/__init__.py`. Never recreate `__init__.py`; add a line to it.
- Use `TransactionCase` and tag classes `@tagged('post_install', '-at_install')`, so they run on a fully loaded database.
- Build test data in `setUpClass`; never rely on demo data.
- Every new model gets an access-rights test: a user without the right role must not read or write it.
