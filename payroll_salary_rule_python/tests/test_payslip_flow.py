# Part of Odoo. See LICENSE file for full copyright and licensing details.


from .common import TestPayslipBase


class TestPayslipFlow(TestPayslipBase):
    def setUp(self):
        super().setUp()

        self.test_rule = self.SalaryRule.create(
            {
                "name": "Test rule",
                "code": "TEST",
                "category_id": self.categ_alw.id,
                "sequence": 5,
                "amount_select": "code",
                "amount_python_compute": "result = contract.wage",
            }
        )

    def test_contract_qty(self):

        # I set the test rule to detect contract count
        self.test_rule.amount_python_compute = (
            "result = payroll.contracts and payroll.contracts.count or -1.0"
        )
        self.developer_pay_structure.write({"rule_ids": [(4, self.test_rule.id)]})

        # I put all eligible contracts (including Richard's) in an "open" state
        self.apply_contract_cron()

        # I create an employee Payslip and process it
        richard_payslip = self.Payslip.create({"employee_id": self.richard_emp.id})
        richard_payslip.onchange_employee()
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Test line")
        self.assertEqual(
            line[0].amount, 1.0, "The calculated dictionary value 'contracts.qty' is 1"
        )

    # def test_00_payslip_flow(self):
    #     # Find the 'NET' payslip line and check that it adds up
    #     # salary + HRA + MA + SALE - PT
    #     work100 = richard_payslip.worked_days_line_ids.filtered(
    #         lambda x: x.code == "WORK100"
    #     )
    #     line = richard_payslip.line_ids.filtered(lambda l: l.code == "BASIC")
    #     self.assertEqual(len(line), 1, "I found the 'BASIC' line")
    #     self.assertEqual(
    #         line[0].amount,
    #         5000.0 + (0.4 * 5000) + (work100.number_of_days * 10) + 0.05 - 200.0,
    #         "The 'NET' amount equals salary plus allowances - deductions",
    #     )
