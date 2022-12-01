from datetime import date

from odoo.tests.common import TransactionCase


class TestTimeParameter(TransactionCase):
    def setUp(self):
        super().setUp()

    def test_time_parameter(self):
        self.env["base.time.parameter"].create(
            {
                "code": "TEST_CODE",
                "type": "string",
                "version_ids": [
                    (0, 0, {"date_from": date(2022, 1, 1), "value": "TEST_VALUE"})
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

        time_value = payslip.get_time_parameter("TEST_CODE")
        rule_value = payslip.get_time_parameter("TEST_CODE")
        self.assertEqual(time_value, "TEST_VALUE", "value = TEST_VALUE")
        self.assertEqual(rule_value, "TEST_VALUE", "value = TEST_VALUE")
