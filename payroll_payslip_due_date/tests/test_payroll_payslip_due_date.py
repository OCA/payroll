# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import tagged
from odoo.tests.common import SavepointCase


@tagged("post_install", "-at_install")
class TestPayslipDueDate(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.company.payroll_payslip_due_workdays = 5

        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "Test Payroll Calendar",
                "tz": "UTC",
                "company_id": cls.company.id,
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Mon",
                            "dayofweek": "0",
                            "hour_from": 8.0,
                            "hour_to": 16.0,
                            "day_period": "morning",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Tue",
                            "dayofweek": "1",
                            "hour_from": 8.0,
                            "hour_to": 16.0,
                            "day_period": "morning",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Wed",
                            "dayofweek": "2",
                            "hour_from": 8.0,
                            "hour_to": 16.0,
                            "day_period": "morning",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Thu",
                            "dayofweek": "3",
                            "hour_from": 8.0,
                            "hour_to": 16.0,
                            "day_period": "morning",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Fri",
                            "dayofweek": "4",
                            "hour_from": 8.0,
                            "hour_to": 16.0,
                            "day_period": "morning",
                        },
                    ),
                ],
            }
        )

        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "company_id": cls.company.id,
                "resource_calendar_id": cls.calendar.id,
            }
        )

        cls.contract = cls.env["hr.contract"].create(
            {
                "name": "Test Contract",
                "employee_id": cls.employee.id,
                "company_id": cls.company.id,
                "date_start": "2026-01-01",
                "wage": 1000.0,
                "resource_calendar_id": cls.calendar.id,
            }
        )

    def _create_payslip(self, date_from="2026-02-01", date_to="2026-02-28"):
        return self.env["hr.payslip"].create(
            {
                "name": "Test Payslip",
                "employee_id": self.employee.id,
                "contract_id": self.contract.id,
                "date_from": date_from,
                "date_to": date_to,
            }
        )

    def test_due_date_workdays(self):
        payslip = self._create_payslip(date_to="2026-02-28")
        self.assertEqual(str(payslip.payment_due_date), "2026-03-06")

    def test_due_date_zero_workdays(self):
        self.company.payroll_payslip_due_workdays = 0
        payslip = self._create_payslip(date_to="2026-02-28")
        self.assertEqual(str(payslip.payment_due_date), "2026-02-28")

    def test_due_date_skips_calendar_leaves(self):
        self.company.payroll_payslip_due_workdays = 5
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Holiday",
                "calendar_id": self.calendar.id,
                "date_from": "2026-03-04 00:00:00",
                "date_to": "2026-03-04 23:59:59",
            }
        )
        payslip = self._create_payslip(date_to="2026-02-28")
        self.assertEqual(str(payslip.payment_due_date), "2026-03-09")
