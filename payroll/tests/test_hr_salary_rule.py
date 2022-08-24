# Part of Odoo. See LICENSE file for full copyright and licensing details.

from .common import TestPayslipBase


class TestSalaryRule(TestPayslipBase):
    def setUp(self):
        super().setUp()

        self.Payslip = self.env["hr.payslip"]
        self.Rule = self.env["hr.salary.rule"]

        self.test_rule = self.Rule.create(
            {
                "name": "test rule",
                "code": "TEST",
                "category_id": self.env.ref("payroll.ALW").id,
                "sequence": 6,
                "amount_select": "code",
                "amount_python_compute": "result = 0",
            }
        )
        self.developer_pay_structure.write({"rule_ids": [(4, self.test_rule.id)]})

    def test_python_code_return_values(self):

        self.test_rule.amount_python_compute = (
            "result_rate = 0\n" "result_qty = 0\n" "result = 0\n"
        )

        # Open contracts
        cc = self.env["hr.contract"].search([("employee_id", "=", self.richard_emp.id)])
        cc.kanban_state = "done"
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

        # Create payslip and compute
        payslip = self.Payslip.create({"employee_id": self.richard_emp.id})
        payslip.onchange_employee()
        payslip.compute_sheet()

        line = payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Test line")
        self.assertEqual(line.amount, 0.0, "The amount is zero")
        self.assertEqual(line.rate, 0.0, "The rate is zero")
        self.assertEqual(line.quantity, 0.0, "The quantity is zero")

    def test_python_code_result_not_set(self):

        self.test_rule.amount_python_compute = "result = 2"

        # Open contracts
        cc = self.env["hr.contract"].search([("employee_id", "=", self.richard_emp.id)])
        cc.kanban_state = "done"
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

        # Create payslip and compute
        payslip = self.Payslip.create({"employee_id": self.richard_emp.id})
        payslip.onchange_employee()
        payslip.compute_sheet()

        line = payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Test line")
        self.assertEqual(line.amount, 2.0, "The amount is zero")
        self.assertEqual(line.rate, 100.0, "The rate is zero")
        self.assertEqual(line.quantity, 1.0, "The quantity is zero")
