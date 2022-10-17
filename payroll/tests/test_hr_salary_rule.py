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
                "amount_select": "fix",
                "amount_fix": 0.0,
            }
        )
        self.developer_pay_structure.write({"rule_ids": [(4, self.test_rule.id)]})
