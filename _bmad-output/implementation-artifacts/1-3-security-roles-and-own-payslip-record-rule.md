---
baseline_commit: 9664f1d433a65762ee2eaab6538bb691d359b5ce
---

# Story 1.3: Security roles and own-payslip record rule

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->
<!-- Ultimate context engine analysis completed - comprehensive developer guide created (batch-created 2026-07-08 from epics EN v1.0D + ARCHITECTURE-SPINE + PRD v3.0D + Story 1.1 learnings). -->

## Story

As a system administrator,
I want four least-privilege roles and an own-payslip record rule,
so that each user can access only what their role permits.

## Acceptance Criteria

1. **Given** the security data, **Then** four groups exist: Employee, Payroll User, Payroll Manager, and Accountant. *(FR026)*
2. **Given** an Employee user, **When** they open payslips, **Then** a record rule limits them to records where `employee_id.user_id = user`. *(FR027)*
3. **Given** each custom model, **Then** `ir.model.access` entries grant least-privilege CRUD aligned to the four roles.
4. **Given** the most senior existing role is Payroll Manager, **Then** no new group is introduced (the distribution gate reuses `group_l10n_cw_payroll_manager`). *(AR019)*

## Tasks / Subtasks

- [x] **Task 1 — Create the four security groups** (AC: 1, 4)
  - [x] Create `security/hr_payroll_security.xml` with a module category (`ir.module.category`, Dutch name, e.g. "Salarisadministratie Curaçao") and the four groups: `group_l10n_cw_employee`, `group_l10n_cw_payroll_user`, `group_l10n_cw_payroll_manager`, `group_l10n_cw_accountant`.
  - [x] Set `implied_ids` so Manager implies User (standard Odoo group laddering); Employee and Accountant stand alone.
  - [x] Do NOT create any additional group — the payslip-distribution gate (Story 3.6) reuses `group_l10n_cw_payroll_manager` (AD-16).
- [x] **Task 2 — Own-payslip record rule** (AC: 2)
  - [x] Add `ir.rule` `rule_payslip_employee_own` on `hr_payroll.model_hr_payslip`, groups `group_l10n_cw_employee`, `domain_force = [('employee_id.user_id', '=', user.id)]` (exact XML in PRD §Security and Access Control).
- [x] **Task 3 — ir.model.access baseline + growth convention** (AC: 3)
  - [x] Create `security/ir.model.access.csv`. Custom models do not exist yet (they arrive in Stories 1.4/1.7/1.10 and 2.x) — seed the file with access rows for **existing** models the roles need (e.g. read on `hr.payslip` for the Employee group if not already granted by `hr_payroll` defaults) and establish the convention: **each later story that creates a model adds its own access rows in the same commit**. Never add a row for a model that doesn't exist yet (install fails — same class of error as the 1.1 manifest guardrail).
  - [x] Document the intended CRUD matrix (see Dev Notes) as a comment header in the CSV so later stories fill it consistently.
- [x] **Task 4 — Wire into manifest and verify** (AC: 1–3)
  - [x] Add `security/ir.model.access.csv` and `security/hr_payroll_security.xml` to the manifest `data` list (security files first — Odoo convention, and later data files may reference the groups).
  - [x] Dev-side: XML/CSV lint; manifest parse. PO-side: install/update smoke test; log in as a test employee user and confirm only own payslips are visible.

### Review Findings

- [x] [Review][Decision] Medewerker and Accountant can read `hr.payslip` but not its lines, worked days or inputs, have no menu, and cannot print — **Resolved 2026-10-06 (PO): defer** the usable employee/accountant payslip UI (child-model read, menu, PDF download) to Stories 3.6/4.1, where the screens and the PDF are built; record the deferral in the PRD and epics (patch below). Original detail: Opening a payslip form or report reads `hr.payslip.line`/`.worked_days`/`.input` (core grants these to `hr_payroll.group_hr_payroll_user` only) and would raise AccessError; the Payroll menu is limited to payroll users; `/print/payslips` refuses non-payroll users. The PRD Employee row still promises "view and download own payslips". Either grant read on the child models now (with own-record rules for Medewerker), or defer the usable employee/accountant UI to the distribution/PDF stories (3.6/4.1) and record that deferral in the PRD and epics.
- [x] [Review][Decision] The own-payslip rule ignores payslip state — **Resolved 2026-10-06 (PO): restrict now** to final states (`validated`, `paid`); becomes the patch below. Original detail: Employees could see draft or not-yet-final payslips (states `draft`/`validated`/`paid`/`cancel`) before the run is closed. Either restrict the rule to final states now, or leave the rule as is and let the distribution story (3.6, AD-16) control what employees see.
- [x] [Review][Patch] Record the deferral of employee/accountant payslip viewing and download to Stories 3.6/4.1 in the PRD Users and Roles section and epics EN+NL (resolved decision) [docs/prd/PRD - v3.0D.md; epics EN/NL]
- [x] [Review][Patch] Restrict `rule_payslip_employee_own` to `state in ('validated', 'paid')`, add a test, and update the rule wherever the specs state it (PRD §Security XML, epics FR027 + Story 1.3 AC2 EN+NL, spine Audit & access, `.memlog.md`) (resolved decision) [l10n_cw_hr_payroll/security/hr_payroll_security.xml]
- [x] [Review][Patch] Accountant who also holds Medewerker is cut down to own payslips — add an all-payslips rule for `group_l10n_cw_accountant` (Gebruiker/Manager are already covered by core `hr_payroll_rule_officer`), plus a test for the combination [l10n_cw_hr_payroll/security/hr_payroll_security.xml]
- [x] [Review][Patch] Medewerker does not imply `base.group_user`, so it could be given to portal/share users — imply it [l10n_cw_hr_payroll/security/hr_payroll_security.xml]
- [x] [Review][Patch] Test gaps: no Gebruiker-only test; Accountant run read/no-write untested; journal-entry test only checks group membership (should read `account.move`); employee create/unlink not checked; Manager behaviour not checked [l10n_cw_hr_payroll/tests/test_security.py]
- [x] [Review][Patch] Story record: "If accepted" wording left after the decision; File List sprint-status line says "in-progress" (now review) [this story file]
- [x] [Review][Patch] Epics Story 1.3 AC3 (EN+NL) has no pointer to the 2026-10-06 role-scope decision [_bmad-output/planning-artifacts/Odoo Module Design Epics - EN/NL - v1.0D.md]
- [x] [Review][Patch] `docs/README.md` lacks the Title/Subtitle blocks the other docs use [docs/README.md]
- [x] [Review][Defer] Own-payslip rule follows whoever is currently linked to the employee; re-linking `user_id` moves the payslip history to the new user [l10n_cw_hr_payroll/security/hr_payroll_security.xml] — deferred, inherent to Odoo's `employee_id.user_id` pattern
- [x] [Review][Defer] Security records are not `noupdate`, so database-side edits are reset on upgrade [l10n_cw_hr_payroll/security/hr_payroll_security.xml] — deferred, decide before production
- [x] [Review][Defer] Users holding core Payroll Officer/Administrator without a CW role keep full payslip access, outside the CW role model [AD-16] — deferred to Story 3.6 (distribution gate must not be bypassable via core sending paths)
- [x] [Review][Defer] Dutch role names drift: code "Gebruiker/Manager", NL FR026 "Salarisgebruiker/Salarisbeheerder", NL Story 1.3 "Payroll-gebruiker/Payroll-manager" [epics NL] — deferred, pre-existing naming

## Dev Notes

### Role capability matrix (PRD §Users and Roles — the target CRUD baseline)

| Role | Group | Capabilities |
|---|---|---|
| Employee | `group_l10n_cw_employee` | View and download own payslips only |
| Payroll User | `group_l10n_cw_payroll_user` | Compute runs, edit employee wage lines and payslip descriptions, read tax brackets |
| Payroll Manager | `group_l10n_cw_payroll_manager` | Full access incl. tax bracket / SVB parameter / lb-tabel management and reopening closed runs |
| Accountant | `group_l10n_cw_accountant` | Read payroll runs and journal entries; no write access to computation |

Fine-grained per-group rights are **OQ-04 (deferred detail design)** — implement the coarse matrix above; don't invent finer permissions.

### Constraints and gotchas

- **AD-16:** Payroll Manager is deliberately the most senior group; distribution (3.6) and Lei di Bion beschikking approval (2.9) both hang off it. Naming must be exactly `group_l10n_cw_payroll_manager` — later stories reference it by XML id.
- **AD-19 (company scoping):** operational models get multi-company record rules when they are created (1.7/1.10); this story only establishes groups + the payslip rule. Don't pre-create record rules for nonexistent models.
- Payroll data protection (NFR006): least privilege is the statutory baseline (Landsverordening bescherming persoonsgegevens) — when in doubt, grant less; the PO can widen later.
- `hr_payroll` (Enterprise) ships its own groups (`hr_payroll.group_hr_payroll_user`/`_manager`). Do not replace them; the four CW groups are module-level roles. Check in the Enterprise checkout (`/home/nroosje/dev/odoo-sh/enterprise-19.0/hr_payroll/security/`) how peer localizations relate their groups to the core payroll groups (e.g. via `implied_ids`) and follow that convention.

### Previous story intelligence (Story 1.1)

- Install-ordering guardrail: only list files in `data` that exist in this commit. This story's two security files are created here, so listing them is safe.
- Verification protocol: dev-side static checks; live install smoke test delegated to PO (no Odoo runtime in sandbox). Enterprise checkout at `/home/nroosje/dev/odoo-sh/enterprise-19.0/` is read-only reference.
- Odoo 19: no `hr.contract`; anything contract-ish is `hr.version` (D1).

### Project Structure Notes

- Files: `security/hr_payroll_security.xml` (new), `security/ir.model.access.csv` (new), `__manifest__.py` (data list). Remove `security/.gitkeep`.
- Matches Tech Design §13 tree (`security/ir.model.access.csv`, `security/hr_payroll_security.xml`).

### Testing standards

- No `tests/` package yet. When models+behavior exist (1.4+), add security regression tests (e.g. `TransactionCase` asserting an employee user cannot read another employee's payslip). Note that intent in the CSV header comment so the 1.4+ dev picks it up.

### References

- [Source: _bmad-output/planning-artifacts/Odoo Module Design Epics - EN - v1.0D.md#Story 1.3; #FR026, FR027; #AR019]
- [Source: docs/prd/PRD - v3.0D.md#Users and Roles; #Security and Access Control (record-rule XML); #Data Protection]
- [Source: _bmad-output/planning-artifacts/architecture/architecture-l10n_cw_hr_payrol-2026-06-25/ARCHITECTURE-SPINE.md#AD-16, AD-19; #Consistency Conventions (Audit & access)]
- [Source: docs/tech_design_l10n_cw_hr_payroll_v3.0D.txt#12.1 User Groups, #12.2 Record Rules]
- [Source: _bmad-output/implementation-artifacts/1-1-greenfield-module-skeleton-and-manifest.md#Dev Notes (install-ordering guardrail)]

## Dev Agent Record

### Agent Model Used

Claude Opus 5.5 (claude-opus-5-5)

### Debug Log References

- Static checks (2026-10-05): manifest parses and every `data` file exists; security XML well-formed (6 records); CSV header matches Odoo's 8 columns, 3 rows, every `group_id` defined in the XML, every `model_id` prefixed `hr_payroll.`; all in-module `ref()`s resolve to earlier records; tests compile. No Odoo runtime here, so the tests were not executed (same protocol as 1.1/1.2).

### Completion Notes List

- **Groups (AC1, AC4):** `security/hr_payroll_security.xml` defines four groups under one privilege "Salarisadministratie Curaçao": Medewerker (`group_l10n_cw_employee`), Accountant (`group_l10n_cw_accountant`), Gebruiker (`group_l10n_cw_payroll_user`), Manager (`group_l10n_cw_payroll_manager`). No fifth group; the Manager XML comment records that distribution (AD-16) and beschikking approval reuse it.
- **Odoo 19 deviation, privilege instead of category:** Task 1 asks for an `ir.module.category`. Odoo 19 groups hang off `res.groups.privilege` (`privilege_id`), whose `category_id` is `base.module_category_human_resources`, the same pattern `hr_payroll` uses. No living spec prescribes `ir.module.category`, so no spec change was needed.
- **Laddering:** Manager implies Gebruiker (Task 1). Two additions, both required for the roles to grant anything: Gebruiker implies `hr_payroll.group_hr_payroll_user` and Manager implies `hr_payroll.group_hr_payroll_manager`. All core payroll ACLs are bound to those groups, and no peer localization defines its own groups (26 checked), so implying them is the only way short of duplicating every core ACL. **Least-privilege trade-off for the PO (NFR006):** `hr_payroll.group_hr_payroll_user` implies `hr.group_hr_user`, so a CW Gebruiker can also manage employee records. Accountant implies `account.group_account_readonly`, which covers "read journal entries". Medewerker implies `base.group_user` (added in review, so the role cannot go to portal users).
- **Own-payslip rule (AC2):** `rule_payslip_employee_own` exactly as in PRD §Security and Access Control, written with `Command.link`.
- **Access rows (AC3):** the CSV grants read on `hr.payslip` to Medewerker (paired with the own rule) and read on `hr.payslip` + `hr.payslip.run` to Accountant. No custom models exist yet. `hr.payslip.line` is deliberately not granted: without a matching rule, Medewerker would see every employee's lines.
- **Deviation, CRUD matrix location:** Task 3 asks for a comment header in the CSV. Odoo's CSV loader reads the first row as the column header and has no comment syntax, so a comment row would break the install. The matrix and the growth convention live in an XML comment at the top of `hr_payroll_security.xml` instead.
- **Load order:** `data` lists the XML before the CSV (Task 4 names them the other way round), because the CSV references the XML's groups.
- **Tests start in this story:** the PO's manual check may be impossible, because non-payroll users have no payroll menu and `/print/payslips` refuses anyone without `hr_payroll.group_hr_payroll_user`. So `tests/test_security.py` (`post_install`) proves AC2 and the role ladder: own payslip only, no read of another's, no write, no access without a CW group, Accountant reads all but cannot write, Accountant has journal read, Manager ladders to the CW and core payroll groups. Story 1.4 assumes it creates the first `tests/` package; it now extends this one.
- **Known edges:**
  - Payslip PDF download for employees is not possible yet. The standard print route requires payroll-user rights, so this arrives with distribution/PDF (Stories 3.6/4.1).
  - Fixed in review: a user holding both Medewerker and Accountant was narrowed to their own payslips (Odoo ORs group rules); `rule_payslip_accountant_all` now keeps the Accountant's full read.
  - How Odoo 19 renders four partly-unchained groups under one privilege on the user form is unverified (PO check below).
- **Roles documented in the manifest `description`** (new key after `summary`): the four roles and what each includes, for the Apps page. The Odoo output style asks for groups to be documented there; the project has no `docs/reference/` tree, and the global rules forbid unrequested doc files, so the manifest description is the chosen place.
- **Test fixture:** employees get a contract starting 2025-01-01 (`date_version`, `contract_date_start`), so the January 2026 payslips fall inside a version, as in `hr_payroll/tests/common.py`.
- **Story 1.4 protected:** its Task 5 carries a dated note to extend, not recreate, `tests/__init__.py`.
- **PO decision (NFR006) — accepted 2026-10-06:** the working role mapping is wider than the PRD matrix: Gebruiker also manages employee records (`hr.group_hr_user`), Manager gets full HR administration (`hr.group_hr_manager`), and Accountant reads every payslip. PRD "Users and Roles", epics EN+NL FR026, the spine's Audit & access row and `.memlog.md` were updated the same day.
- **Open, PO verification:**
  1. **Done 2026-10-05:** upgrade with tests on `caribware_dev_19_01` loaded both security files and passed `0 failed, 0 error(s) of 7 tests`; the log shows each denial at the expected layer (ACL for write and no-group read, record rule for another employee's payslip). Original instruction: upgrade with tests: `odoo -c /etc/odoo/odoo.conf -d caribware_dev_19_01 -u l10n_cw_hr_payroll --test-enable --stop-after-init --http-port=8099` in the Coolify container. Expect `0 failed, 0 error(s)` with 7 tests from `test_security`.
  2. On a user form (Settings → Users), confirm each of the four roles can be assigned under "Salarisadministratie Curaçao".
  3. If only `test_user_without_cw_group_has_no_payslip_access` fails, another installed module grants internal users read on `hr.payslip`. Investigate that leak; do not relax the test.

### File List

- `l10n_cw_hr_payroll/security/hr_payroll_security.xml` (new)
- `l10n_cw_hr_payroll/security/ir.model.access.csv` (new)
- `l10n_cw_hr_payroll/security/.gitkeep` (deleted)
- `l10n_cw_hr_payroll/tests/__init__.py` (new)
- `l10n_cw_hr_payroll/tests/test_security.py` (new)
- `l10n_cw_hr_payroll/__manifest__.py` (modified: `description`, `data` list)
- `l10n_cw_hr_payroll/security/hr_payroll_security.xml` (review: state filter, accountant all-payslips rule, Medewerker implies `base.group_user`)
- `_bmad-output/implementation-artifacts/1-4-dated-statutory-data-models-and-lookup-methods.md` (Task 5 note: extend the existing `tests/` package)
- `docs/prd/PRD - v3.0D.md`, epics EN+NL (FR026), spine + `.memlog.md` (role scope decision)
- `.gitignore` (`.playwright-mcp/`)
- `docs/guides/testing.md` (new — how to run and read the module tests)
- `docs/README.md` (new — docs index)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (1-3: ready-for-dev → in-progress → review → in-progress after review patches)
- `_bmad-output/implementation-artifacts/deferred-work.md` (review defers)
- `_bmad-output/implementation-artifacts/1-3-security-roles-and-own-payslip-record-rule.md` (this file)

## Change Log

- 2026-10-05: Implemented Tasks 1–3 and the dev-side part of Task 4: four groups under an Odoo 19 privilege, own-payslip rule, baseline access rows, manifest wiring, and a first `tests/` package with 7 security tests. Deviations: privilege instead of module category (Odoo 19), CRUD matrix in the XML instead of the CSV (CSV has no comments), XML loaded before CSV. Also added the manifest `description` documenting the roles, and a note in Story 1.4 to keep the existing `tests/` package. Status stays in-progress until the PO runs the tests, checks the user form, and decides on the wider role mapping.
- 2026-10-05: PO ran the upgrade with `--test-enable`: both security files loaded, 7/7 security tests passed. Still open: user-form role check and the PO decision on the wider role mapping.
- 2026-10-05: Added `docs/guides/testing.md` (test command, flag-by-flag explanation, purpose, reading the result) and a `docs/README.md` index, at the PO's request.
- 2026-10-05: Found that the `-u … --test-enable` run is rolled back on this Odoo 19 build: the module was `installed` but had no XML IDs, so the roles never reached the database. Fix: upgrade without `--test-enable`, then test. `docs/guides/testing.md` now separates the two steps.
- 2026-10-05: PO upgraded without `--test-enable`: all 9 XML IDs (privilege, 4 groups, own-payslip rule, 3 access rows) are now in `caribware_dev_19_01`. Still open: user-form role check and the role-scope decision.
- 2026-10-06: User-form check done in the browser (admin login, read-only): Settings → Users → user form shows "Salarisadministratie Curaçao" under Human Resources, next to Odoo's "Payroll", as a single dropdown with No / Medewerker / Accountant / Gebruiker / Manager. Nothing was changed. Still open: the PO decision on the wider role mapping.
- 2026-10-06: PO accepted the wider role scope; PRD "Users and Roles", epics EN+NL FR026 and the spine's Audit & access row updated with dated notes, decision logged in `.memlog.md`. Live checks done (7/7 tests; roles saved and assignable on the user form; own-payslip behaviour proven by the tests, which replace the manual employee login). Task 4 complete; status → review.
- 2026-10-06: Code review (Blind Hunter, Edge Case Hunter, Acceptance Auditor): 2 decisions, 6 patches, 4 defers, 9 dismissed. PO decisions: defer usable employee/accountant payslip viewing and download to Stories 3.6/4.1 (recorded in PRD + epics); restrict the own-payslip rule to final states now. All 8 patches applied: rule `state in ('validated', 'paid')`; new `rule_payslip_accountant_all`; Medewerker implies `base.group_user`; tests grown from 7 to 13 (own final only, own draft hidden, employee cannot write/create/delete, internal-only role, accountant run read/no write, accountant journal read via `has_access`, accountant+employee combo, payroll user reads/edits all, manager reads all); manifest description, PRD (Users and Roles, Security XML), epics EN+NL (FR027, Story 1.3 AC2/AC3, Story 3.6/4.1 notes), spine Audit & access, `.memlog.md`, `docs/guides/testing.md`, `docs/README.md` and `deferred-work.md` updated. Static checks pass; not yet run on Odoo. Status → in-progress until the PO reruns the upgrade and the 13 tests.
- 2026-10-06: PO test run after the review patches: 12 passed, 1 error in `setUp` (`has_wrong_data` compute compared `version_id.last_modified_date` with an empty `done_date`). Cause: the fixture set `state='validated'` without `done_date`, which `hr_payroll` sets on validation. Fixture fixed; the accountant+employee combination test passed, so Odoo allows two roles of one privilege on a user.
- 2026-10-06: PO reran the tests: `0 failed, 0 error(s) of 13 tests`. All review findings resolved (2 decisions, 8 patches; 4 deferred). Status → done.
