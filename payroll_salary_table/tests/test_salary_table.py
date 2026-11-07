from odoo.addons.payroll.tests.common import TestPayslipBase


class TestPayslipSalaryTable(TestPayslipBase):
    def setUp(self):
        super().setUp()

        self.salary_table_template = self.env["hr.salary.table.template"].create(
            {"name": "Basic Salary Table", "code": "BASIC"}
        )
        self.salary_table = self.env["hr.salary.table"].create(
            {"template_id": self.salary_table_template.id}
        )
        table_id = self.salary_table.id

        line_values = [
            {
                "table_id": table_id,
                "salary_rule_id": self.rule_basic.id,
                "number_from": 0,
                "number_to": 1,
                "result": 100,
            },
            {
                "table_id": table_id,
                "salary_rule_id": self.rule_basic.id,
                "number_from": 1,
                "number_to": 2,
                "result": 200,
            },
            {
                "table_id": table_id,
                "salary_rule_id": self.rule_basic.id,
                "number_from": 2,
                "number_to": 3,
                "result": 300,
            },
        ]
        self.env["hr.salary.table.line"].create(line_values)

    def test_salary_table(self):
        payslip = self.Payslip.create(
            {
                "employee_id": self.richard_emp.id,
                "contract_id": self.richard_contract.id,
            }
        )
        payslip.onchange_employee()

        self.rule_basic.amount_python_compute = "result = lookup_table('BASIC', 0)"
        payslip.compute_sheet()
        line = payslip.line_ids.filtered(lambda record: record.code == "BASIC")
        self.assertEqual(line.amount, 100)

        self.rule_basic.amount_python_compute = "result = lookup_table('BASIC', 1)"
        payslip.compute_sheet()
        line = payslip.line_ids.filtered(lambda record: record.code == "BASIC")
        self.assertEqual(line.amount, 200)

        self.rule_basic.amount_python_compute = "result = lookup_table('BASIC', 2)"
        payslip.compute_sheet()
        line = payslip.line_ids.filtered(lambda record: record.code == "BASIC")
        self.assertEqual(line.amount, 300)
