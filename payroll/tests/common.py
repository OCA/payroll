# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo.fields import Date
from odoo.tests.common import TransactionCase


class TestPayslipBase(TransactionCase):
    def setUp(self):
        super(TestPayslipBase, self).setUp()

        self.Payslip = self.env["hr.payslip"]

        # Some salary rules references
        self.hra_rule_id = self.ref("payroll.hr_salary_rule_houserentallowance1")
        self.conv_rule_id = self.ref("payroll.hr_salary_rule_convanceallowance1")
        self.prof_tax_rule_id = self.ref("payroll.hr_salary_rule_professionaltax1")
        self.pf_rule_id = self.ref("payroll.hr_salary_rule_providentfund1")
        self.mv_rule_id = self.ref("payroll.hr_salary_rule_meal_voucher")
        self.comm_rule_id = self.ref("payroll.hr_salary_rule_sales_commission")
        self.basic_rule_id = self.ref("payroll.hr_rule_basic")
        self.gross_rule_id = self.ref("payroll.hr_rule_taxable")
        self.net_rule_id = self.ref("payroll.hr_rule_net")

        # I create a new employee "Richard"
        self.richard_emp = self.env["hr.employee"].create(
            {
                "name": "Richard",
                "gender": "male",
                "birthday": "1984-05-01",
                "country_id": self.ref("base.be"),
                "department_id": self.ref("hr.dep_rd"),
            }
        )

        # I create a salary structure for "Software Developer"
        self.developer_pay_structure = self.env["hr.payroll.structure"].create(
            {
                "name": "Salary Structure for Software Developer",
                "code": "SD",
                "company_id": self.ref("base.main_company"),
                "rule_ids": [
                    (4, self.hra_rule_id),
                    (4, self.conv_rule_id),
                    (4, self.prof_tax_rule_id),
                    (4, self.pf_rule_id),
                    (4, self.mv_rule_id),
                    (4, self.comm_rule_id),
                    (4, self.basic_rule_id),
                    (4, self.gross_rule_id),
                    (4, self.net_rule_id),
                ],
            }
        )

        # I create a contract for "Richard"
        self.env["hr.contract"].create(
            {
                "date_end": Date.to_string(datetime.now() + timedelta(days=365)),
                "date_start": Date.today(),
                "name": "Contract for Richard",
                "wage": 5000.0,
                "employee_id": self.richard_emp.id,
                "struct_id": self.developer_pay_structure.id,
                "kanban_state": "done",
            }
        )

    def apply_contract_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()
