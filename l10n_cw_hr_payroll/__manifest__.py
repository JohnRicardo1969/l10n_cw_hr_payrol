# -*- coding: utf-8 -*-
{
    'name': 'Payroll — Curaçao',
    'version': '19.0.0.1.0',
    # 'Human Resources/Payroll' matches all shipped Odoo payroll localizations
    # (l10n_*_hr_payroll) — required for a future official-localization track.
    'category': 'Human Resources/Payroll',
    'summary': 'Curaçao payroll localization: loonbelasting, SVB premiums, three-tier wage model',
    'description': """
Payroll — Curaçao
=================

Statutory payroll for Curaçao (loonbelasting and SVB premiums) on the Odoo
Payroll engine. Monthly payroll only in this release.

Security roles
--------------

Assign one role per user under "Salarisadministratie Curaçao":

* **Medewerker** - sees only their own final (validated or paid) payslips.
  Viewing the payslip details and downloading the PDF arrive with payslip
  distribution and the payslip PDF.
* **Accountant** - reads payroll runs, payslips and journal entries; cannot
  change anything. Includes Accounting read-only access.
* **Gebruiker** - computes payroll runs and edits employee wage lines. Includes
  the Payroll Officer role, which also lets the user manage employee records.
* **Manager** - full access, including statutory rates and reopening closed
  runs. Includes Gebruiker and the Payroll Administrator role.
""",
    'author': 'Caribware',
    'license': 'OPL-1',
    'countries': ['cw'],
    # NOTE: no 'hr_contract' — removed in Odoo 19; contracts are absorbed into
    # core 'hr' as the hr.version model (decided 2026-07-07, review D1).
    'depends': [
        'hr',
        'hr_holidays',
        'hr_payroll',
        'hr_payroll_account',
        'hr_attendance',
    ],
    # Data files are added incrementally by later stories as the referenced files
    # are created. Do NOT list a file here before it exists: Odoo fails to install
    # a module whose manifest references a missing data file.
    # The security XML goes first: the CSV rows reference its groups by XML id.
    'data': [
        'security/hr_payroll_security.xml',
        'security/ir.model.access.csv',
    ],
    # No 'assets' key: the module uses Odoo 19's default look and ships no
    # stylesheet (AD-15, decided 2026-10-05).
    'installable': True,
    'application': False,
    'auto_install': False,
}
