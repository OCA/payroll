from datetime import date

from odoo.tests.common import TransactionCase


class TestTimeParameter(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.parameter = cls.env["base.time.parameter"].create(
            {
                "code": "TEST_CODE",
                "type": "string",
                "version_ids": [
                    (0, 0, {"date_from": date(2022, 1, 1), "value": "TEST_VALUE"}),
                    (0, 0, {"date_from": date(2023, 1, 1), "value": "NEW_VALUE"}),
                ],
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Richard",
                "gender": "male",
                "birthday": "1984-05-01",
                "country_id": cls.env.ref("base.be").id,
            }
        )
        cls.payslip = cls.env["hr.payslip"].create(
            {
                "employee_id": cls.employee.id,
                "date_from": date(2022, 6, 1),
                "date_to": date(2022, 6, 30),
            }
        )

    def test_time_parameter(self):
        # Without a date, the value of today is used.
        time_value = self.payslip.get_time_parameter("TEST_CODE")
        self.assertEqual(time_value, "NEW_VALUE", "value = NEW_VALUE")

    def test_rule_parameter(self):
        # This is what a salary rule formula calls: without a date, the value
        # at the start date of the payslip is used, not the value of today.
        rule_value = self.payslip.rule_parameter("TEST_CODE")
        self.assertEqual(rule_value, "TEST_VALUE", "value = TEST_VALUE")

    def test_rule_parameter_date(self):
        rule_value = self.payslip.rule_parameter("TEST_CODE", date=date(2023, 6, 1))
        self.assertEqual(rule_value, "NEW_VALUE", "value = NEW_VALUE")

    def test_rule_parameter_get_date(self):
        # get="date" returns the start date of the version the value comes from
        version_date = self.payslip.rule_parameter("TEST_CODE", get="date")
        self.assertEqual(version_date, date(2022, 1, 1), "date = Jan. 1, 2022")
