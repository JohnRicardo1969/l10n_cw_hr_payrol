from datetime import date

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user

EMPLOYEE_GROUP = 'l10n_cw_hr_payroll.group_l10n_cw_employee'
ACCOUNTANT_GROUP = 'l10n_cw_hr_payroll.group_l10n_cw_accountant'
PAYROLL_USER_GROUP = 'l10n_cw_hr_payroll.group_l10n_cw_payroll_user'
PAYROLL_MANAGER_GROUP = 'l10n_cw_hr_payroll.group_l10n_cw_payroll_manager'


@tagged('post_install', '-at_install')
class TestPayrollSecurity(TransactionCase):
    """Least-privilege roles and the own-payslip record rule (FR026, FR027)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_anna = new_test_user(cls.env, login='cw_anna', groups=EMPLOYEE_GROUP)
        cls.user_ben = new_test_user(cls.env, login='cw_ben', groups=EMPLOYEE_GROUP)
        cls.user_plain = new_test_user(cls.env, login='cw_plain', groups='base.group_user')
        cls.user_accountant = new_test_user(cls.env, login='cw_accountant', groups=ACCOUNTANT_GROUP)
        cls.user_payroll = new_test_user(cls.env, login='cw_payroll', groups=PAYROLL_USER_GROUP)
        cls.user_manager = new_test_user(cls.env, login='cw_manager', groups=PAYROLL_MANAGER_GROUP)

        cls.employee_anna = cls._create_employee('Anna', cls.user_anna)
        cls.employee_ben = cls._create_employee('Ben', cls.user_ben)
        cls.payslip_anna = cls._create_payslip(cls.employee_anna, date(2026, 1, 1), date(2026, 1, 31))
        cls.payslip_anna_draft = cls._create_payslip(cls.employee_anna, date(2026, 2, 1), date(2026, 2, 28))
        cls.payslip_ben = cls._create_payslip(cls.employee_ben, date(2026, 1, 1), date(2026, 1, 31))
        # Only final payslips are visible to employees; the draft stays draft.
        # Validate the way hr_payroll does: done_date is required once a payslip
        # is validated, or its has_wrong_data compute fails.
        (cls.payslip_anna | cls.payslip_ben).write({'state': 'validated', 'done_date': fields.Datetime.now()})
        cls.payslips = cls.payslip_anna | cls.payslip_anna_draft | cls.payslip_ben

        cls.payslip_run = cls.env['hr.payslip.run'].create({
            'name': 'Januari 2026',
            'date_start': date(2026, 1, 1),
            'date_end': date(2026, 1, 31),
        })

    @classmethod
    def _create_employee(cls, name, user):
        # The contract must cover the payslip periods below, otherwise the payslip
        # has no version to compute from.
        return cls.env['hr.employee'].create({
            'name': name,
            'user_id': user.id,
            'date_version': date(2025, 1, 1),
            'contract_date_start': date(2025, 1, 1),
            'wage': 3000.0,
        })

    @classmethod
    def _create_payslip(cls, employee, date_from, date_to):
        return cls.env['hr.payslip'].create({
            'name': f'Loonstrook {employee.name} {date_from:%m-%Y}',
            'employee_id': employee.id,
            'date_from': date_from,
            'date_to': date_to,
        })

    def _visible_payslips(self, user):
        return self.env['hr.payslip'].with_user(user).search([('id', 'in', self.payslips.ids)])

    def test_employee_sees_only_own_final_payslips(self):
        self.assertEqual(self._visible_payslips(self.user_anna), self.payslip_anna)

    def test_employee_cannot_read_other_payslip(self):
        with self.assertRaises(AccessError):
            self.payslip_ben.with_user(self.user_anna).read(['name'])

    def test_employee_cannot_read_own_draft_payslip(self):
        with self.assertRaises(AccessError):
            self.payslip_anna_draft.with_user(self.user_anna).read(['name'])

    def test_employee_cannot_change_payslips(self):
        payslip_model = self.env['hr.payslip'].with_user(self.user_anna)
        with self.assertRaises(AccessError):
            self.payslip_anna.with_user(self.user_anna).write({'name': 'Gewijzigd'})
        with self.assertRaises(AccessError):
            self.payslip_anna.with_user(self.user_anna).unlink()
        with self.assertRaises(AccessError):
            payslip_model.create({
                'name': 'Eigen loonstrook',
                'employee_id': self.employee_anna.id,
                'date_from': date(2026, 3, 1),
                'date_to': date(2026, 3, 31),
            })

    def test_employee_role_is_internal_only(self):
        self.assertTrue(self.env.ref(EMPLOYEE_GROUP).implied_ids & self.env.ref('base.group_user'))

    def test_user_without_cw_group_has_no_payslip_access(self):
        with self.assertRaises(AccessError):
            self.env['hr.payslip'].with_user(self.user_plain).search([])

    def test_accountant_reads_all_payslips_but_cannot_write(self):
        self.assertEqual(self._visible_payslips(self.user_accountant), self.payslips)
        with self.assertRaises(AccessError):
            self.payslip_anna.with_user(self.user_accountant).write({'name': 'Gewijzigd'})

    def test_accountant_reads_runs_but_cannot_change_them(self):
        run = self.payslip_run.with_user(self.user_accountant)
        self.assertEqual(run.read(['name'])[0]['name'], 'Januari 2026')
        with self.assertRaises(AccessError):
            run.write({'name': 'Gewijzigd'})

    def test_accountant_reads_journal_entries(self):
        moves = self.env['account.move'].with_user(self.user_accountant)
        self.assertTrue(moves.has_access('read'))
        self.assertFalse(moves.has_access('write'))

    def test_accountant_who_is_also_employee_still_reads_all_payslips(self):
        self.user_accountant.group_ids |= self.env.ref(EMPLOYEE_GROUP)
        self.assertEqual(self._visible_payslips(self.user_accountant), self.payslips)

    def test_payroll_user_reads_and_edits_all_payslips(self):
        self.assertEqual(self._visible_payslips(self.user_payroll), self.payslips)
        self.payslip_anna_draft.with_user(self.user_payroll).write({'name': 'Gewijzigd door gebruiker'})
        self.assertEqual(self.payslip_anna_draft.name, 'Gewijzigd door gebruiker')

    def test_manager_reads_all_payslips(self):
        self.assertEqual(self._visible_payslips(self.user_manager), self.payslips)

    def test_manager_ladders_to_user_and_core_payroll_groups(self):
        for xmlid in (PAYROLL_USER_GROUP, 'hr_payroll.group_hr_payroll_user', 'hr_payroll.group_hr_payroll_manager'):
            self.assertTrue(self.user_manager.has_group(xmlid), xmlid)
        self.assertFalse(self.user_manager.has_group(EMPLOYEE_GROUP))
