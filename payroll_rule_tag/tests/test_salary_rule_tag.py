from odoo.addons.payroll.tests.common import TestPayslipBase


class TestPayslipSalaryTable(TestPayslipBase):
    def setUp(self):
        super().setUp()

        self.tag_fixed = self.env["hr.salary.rule.tag"].create({"name": "FixedPay"})
        self.tag_taxable = self.env["hr.salary.rule.tag"].create({"name": "Taxable"})
        self.rule_basic.tag_ids = self.tag_fixed | self.tag_taxable
        self.rule_commission.tag_ids = self.tag_taxable

        self.rule_fixed = self.SalaryRule.create(
            {
                "name": "Fixed Pay Total",
                "code": "FIXED_TOTAL",
                "sequence": 20,
                "amount_select": "code",
                "amount_python_compute": "result = tags.FIXEDPAY",
            }
        )
        self.rule_taxable = self.SalaryRule.create(
            {
                "name": "Taxable Total",
                "code": "TAXABLE_TOTAL",
                "sequence": 21,
                "amount_select": "code",
                "amount_python_compute": "result = tags.TAXABLE",
            }
        )
        self.developer_pay_structure.rule_ids |= self.rule_fixed | self.rule_taxable

    def _get_amount(self, payslip, code):
        line = payslip.line_ids.filtered(lambda record: record.code == code)
        return line.amount

    def test_salary_rule_tags(self):
        payslip = self.Payslip.create(
            {
                "employee_id": self.richard_emp.id,
                "contract_id": self.richard_contract.id,
            }
        )
        payslip.onchange_employee()
        payslip.compute_sheet()

        basic = self._get_amount(payslip, "BASIC")
        commission = self._get_amount(payslip, "SALE")
        fixed = self._get_amount(payslip, "FIXED_TOTAL")
        taxable = self._get_amount(payslip, "TAXABLE_TOTAL")

        self.assertEqual(fixed, basic)
        self.assertEqual(taxable, basic + commission)
