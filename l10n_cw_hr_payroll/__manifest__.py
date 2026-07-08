# -*- coding: utf-8 -*-
{
    'name': 'Payroll — Curaçao',
    'version': '19.0.0.1.0',
    # 'Human Resources/Payroll' matches all shipped Odoo payroll localizations
    # (l10n_*_hr_payroll) — required for a future official-localization track.
    'category': 'Human Resources/Payroll',
    'summary': 'Curaçao payroll localization: loonbelasting, SVB premiums, three-tier wage model',
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
    # a module whose manifest references a missing data/asset file. Likewise, the
    # 'assets' bundle (web.assets_backend -> cw_theme_prl10n.scss) is added in
    # Story 1.2 once the stylesheet exists.
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
