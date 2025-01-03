from datetime import date

from odoo.tests.common import TransactionCase


class TestPublicHolidays(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create a resource calendar with 8 hours per day
        self.calendar = self.env["resource.calendar"].create(
            {"name": "Standard 8h/day", "hours_per_day": 8}
        )

        # Create an employee with the above resource calendar
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "resource_calendar_id": self.calendar.id,
            }
        )

        # Create a contract for the employee
        self.contract = self.env["hr.contract"].create(
            {
                "name": "Test Contract",
                "employee_id": self.employee.id,
                "resource_calendar_id": self.calendar.id,
                "date_start": date(2024, 1, 1),
                "wage": 1,
            }
        )

        # Create a public holiday
        self.public_holiday = self.env["hr.holidays.public"].create(
            {
                "year": 2024,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "date": date(2024, 1, 2),
                            "name": "Test Public Holiday",
                        },
                    )
                ],
            }
        )

    def test_compute_public_holidays_days(self):
        """Test public holidays computation for a contract."""
        date_from = date(2024, 1, 1)
        date_to = date(2024, 1, 3)

        public_holidays = self.env["hr.payslip"]._compute_public_holidays_days(
            self.contract, date_from, date_to
        )

        self.assertEqual(
            public_holidays["number_of_days"], 1, "Should have 1 public holiday"
        )
        self.assertEqual(
            public_holidays["number_of_hours"],
            8,
            "Should calculate 8 hours for 1 public holiday",
        )

    def test_get_worked_day_lines(self):
        """Test worked day lines including public holidays."""
        date_from = date(2024, 1, 1)
        date_to = date(2024, 1, 3)

        worked_day_lines = self.env["hr.payslip"].get_worked_day_lines(
            self.contract, date_from, date_to
        )

        # Check that public holidays are included
        public_holiday_lines = [
            line for line in worked_day_lines if line["code"] == "PHOL"
        ]
        self.assertEqual(
            len(public_holiday_lines), 1, "Should include 1 public holiday line"
        )
        self.assertEqual(
            public_holiday_lines[0]["number_of_days"],
            1,
            "Should have 1 public holiday day",
        )
        self.assertEqual(
            public_holiday_lines[0]["number_of_hours"],
            8,
            "Should have 8 hours for public holiday",
        )
