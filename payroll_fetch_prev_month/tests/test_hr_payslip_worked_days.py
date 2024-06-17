from odoo.tests.common import Form

from odoo.addons.payroll.tests.test_hr_payslip_worked_days import TestWorkedDays


class TestWorkedDaysPrevMonth(TestWorkedDays):
    def setUp(self):
        super().setUp()

    def test_worked_days_from_prev_month(self):

        self._common_contract_leave_setup()

        # Set system parameter
        self.env["ir.config_parameter"].sudo().set_param(
            "payroll.worked_days_from_prev_month", True
        )

        # I create an employee Payslip
        frm = Form(self.Payslip)
        frm.employee_id = self.richard_emp
        richard_payslip = frm.save()

        # A leave in the current month should not show when computing the previous month
        worked_days_codes = richard_payslip.worked_days_line_ids.mapped("code")
        self.assertNotIn(
            "TESTLV", worked_days_codes, "The leave is not in the 'Worked Days' list"
        )
