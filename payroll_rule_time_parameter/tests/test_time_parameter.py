from datetime import date

from odoo.tests.common import TransactionCase

from odoo.addons.payroll.models.hr_payslip import Payslips


class TestTimeParameter(TransactionCase):
    def setUp(self):
        super().setUp()

    def test_time_parameter(self):
        self.env["base.time.parameter"].create(
            {
                "code": "TEST_CODE",
                "type": "text",
                "version_ids": [
                    (0, 0, {"date_from": date(2022, 1, 1), "value_text": "TEST_VALUE"})
                ],
            }
        )
        employee = self.env["hr.employee"].create(
            {
                "name": "Richard",
                "gender": "male",
                "birthday": "1984-05-01",
                "country_id": self.ref("base.be"),
            }
        )
        payslip = self.env["hr.payslip"].create(
            {
                "employee_id": employee.id,
            }
        )

        browsable_payslip = Payslips(employee.id, payslip, self.env)
        time_value = browsable_payslip.time_parameter("TEST_CODE")
        rule_value = browsable_payslip.time_parameter("TEST_CODE")
        self.assertEqual(time_value, "TEST_VALUE", "value = TEST_VALUE")
        self.assertEqual(rule_value, "TEST_VALUE", "value = TEST_VALUE")
