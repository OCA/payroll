# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo.tests.common import TransactionCase


class TestPayslipBase(TransactionCase):
    def setUp(self):
        super(TestPayslipBase, self).setUp()

        self.rule_commission = self.SalaryRule.create(
            {
                "name": "Get 1% of sales",
                "code": "SALE",
                "sequence": 17,
                "category_id": self.categ_alw.id,
                "condition_select": "none",
                "amount_select": "code",
                "amount_python_compute": "result = "
                "(inputs.SALEURO and inputs.SALEURO.amount) * 0.01",
            }
        )
        self.RuleInput.create(
            {
                "name": "Sales to Europe",
                "code": "SALEURO",
                "input_id": self.rule_commission.id,
            }
        )

        # Gross
        #
        self.rule_gross = self.SalaryRule.create(
            {
                "name": "Gross",
                "code": "GROSS",
                "sequence": 100,
                "category_id": self.categ_gross.id,
                "condition_select": "none",
                "amount_select": "code",
                "amount_python_compute": "result = categories.BASIC + categories.ALW",
            }
        )

        # Net
        #
        self.rule_net = self.SalaryRule.create(
            {
                "name": "Net",
                "code": "NET",
                "sequence": 200,
                "category_id": self.categ_net.id,
                "condition_select": "none",
                "amount_select": "code",
                "amount_python_compute": "result = categories.BASIC "
                "+ categories.ALW + categories.DED",
            }
        )

        # I update a salary structure for "Software Developer"
        self.developer_pay_structure.write(
            {
                "rule_ids": [
                    (4, self.rule_commission.id),
                    (4, self.rule_gross.id),
                    (4, self.rule_net.id),
                ],
            }
        )
        # I update a salary structure for "Sales Person"
        self.sales_pay_structure.write(
            {
                "rule_ids": [
                    (4, self.rule_commission.id),
                    (4, self.rule_gross.id),
                    (4, self.rule_net.id),
                ],
            }
        )
