# Story 1.3: Security roles and own-payslip record rule

Status: ready-for-dev

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

- [ ] **Task 1 — Create the four security groups** (AC: 1, 4)
  - [ ] Create `security/hr_payroll_security.xml` with a module category (`ir.module.category`, Dutch name, e.g. "Salarisadministratie Curaçao") and the four groups: `group_l10n_cw_employee`, `group_l10n_cw_payroll_user`, `group_l10n_cw_payroll_manager`, `group_l10n_cw_accountant`.
  - [ ] Set `implied_ids` so Manager implies User (standard Odoo group laddering); Employee and Accountant stand alone.
  - [ ] Do NOT create any additional group — the payslip-distribution gate (Story 3.6) reuses `group_l10n_cw_payroll_manager` (AD-16).
- [ ] **Task 2 — Own-payslip record rule** (AC: 2)
  - [ ] Add `ir.rule` `rule_payslip_employee_own` on `hr_payroll.model_hr_payslip`, groups `group_l10n_cw_employee`, `domain_force = [('employee_id.user_id', '=', user.id)]` (exact XML in PRD §Security and Access Control).
- [ ] **Task 3 — ir.model.access baseline + growth convention** (AC: 3)
  - [ ] Create `security/ir.model.access.csv`. Custom models do not exist yet (they arrive in Stories 1.4/1.7/1.10 and 2.x) — seed the file with access rows for **existing** models the roles need (e.g. read on `hr.payslip` for the Employee group if not already granted by `hr_payroll` defaults) and establish the convention: **each later story that creates a model adds its own access rows in the same commit**. Never add a row for a model that doesn't exist yet (install fails — same class of error as the 1.1 manifest guardrail).
  - [ ] Document the intended CRUD matrix (see Dev Notes) as a comment header in the CSV so later stories fill it consistently.
- [ ] **Task 4 — Wire into manifest and verify** (AC: 1–3)
  - [ ] Add `security/ir.model.access.csv` and `security/hr_payroll_security.xml` to the manifest `data` list (security files first — Odoo convention, and later data files may reference the groups).
  - [ ] Dev-side: XML/CSV lint; manifest parse. PO-side: install/update smoke test; log in as a test employee user and confirm only own payslips are visible.

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

### Debug Log References

### Completion Notes List

### File List
