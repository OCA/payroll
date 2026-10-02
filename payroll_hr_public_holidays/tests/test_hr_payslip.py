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
        self.public_holiday = self.env["calendar.public.holiday"].create(
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


class TestPublicHolidaysCountry(TransactionCase):
    """Holidays come from the country and state of the work address."""

    def setUp(self):
        super().setUp()
        self.calendar = self.env["resource.calendar"].create(
            {"name": "Standard 8h/day", "hours_per_day": 8}
        )
        self.country = self.env.ref("base.ar")
        self.other_country = self.env.ref("base.uy")
        self.state = self.env["res.country.state"].search(
            [("country_id", "=", self.country.id)], limit=1
        )
        self.work_address = self.env["res.partner"].create(
            {
                "name": "Workplace",
                "country_id": self.country.id,
                "state_id": self.state.id,
            }
        )
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Employee Without Country",
                "resource_calendar_id": self.calendar.id,
                "address_id": self.work_address.id,
            }
        )
        # The employee's own contact carries no country: the case that used to
        # make every country-specific holiday disappear.
        self.employee.work_contact_id.country_id = False
        self.contract = self.env["hr.contract"].create(
            {
                "name": "Contract",
                "employee_id": self.employee.id,
                "resource_calendar_id": self.calendar.id,
                "date_start": date(2024, 1, 1),
                "wage": 1,
            }
        )

    def _holiday(self, country, day, state=None):
        return self.env["calendar.public.holiday"].create(
            {
                "year": 2024,
                "country_id": country.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "date": day,
                            "name": "Holiday",
                            "state_ids": [(6, 0, state.ids)] if state else [],
                        },
                    )
                ],
            }
        )

    def _days(self):
        return self.env["hr.payslip"]._compute_public_holidays_days(
            self.contract, date(2024, 1, 1), date(2024, 1, 31)
        )["number_of_days"]

    def test_holidays_of_the_work_address_country(self):
        self._holiday(self.country, date(2024, 1, 2))
        self.assertEqual(self._days(), 1)

    def test_holidays_of_another_country_are_ignored(self):
        self._holiday(self.other_country, date(2024, 1, 2))
        self.assertEqual(self._days(), 0)

    def test_state_holidays_follow_the_work_address(self):
        other_state = self.env["res.country.state"].search(
            [("country_id", "=", self.country.id), ("id", "!=", self.state.id)],
            limit=1,
        )
        holiday = self._holiday(self.country, date(2024, 1, 2), state=self.state)
        holiday.line_ids = [
            (
                0,
                0,
                {
                    "date": date(2024, 1, 3),
                    "name": "Other state",
                    "state_ids": [(6, 0, other_state.ids)],
                },
            )
        ]
        self.assertEqual(self._days(), 1)

    def test_without_work_address_the_contact_still_decides(self):
        self.employee.address_id = False
        self.employee.work_contact_id.country_id = self.country
        self._holiday(self.country, date(2024, 1, 2))
        self.assertEqual(self._days(), 1)


class TestPublicHolidaysHours(TransactionCase):
    """PHOL hours come from what the contract calendar schedules that day."""

    def setUp(self):
        super().setUp()
        attendances = [
            (
                0,
                0,
                {
                    "name": str(day),
                    "dayofweek": str(day),
                    "hour_from": 8,
                    "hour_to": 17,
                },
            )
            for day in range(5)
        ] + [(0, 0, {"name": "Sat", "dayofweek": "5", "hour_from": 8, "hour_to": 12})]
        self.calendar = self.env["resource.calendar"].create(
            {"name": "9h weekdays, 4h Saturday", "attendance_ids": attendances}
        )
        # An employee calendar that must NOT be used: the contract's decides.
        other = self.env["resource.calendar"].create(
            {"name": "Employee calendar", "hours_per_day": 1}
        )
        self.employee = self.env["hr.employee"].create(
            {"name": "Hourly Employee", "resource_calendar_id": other.id}
        )
        self.contract = self.env["hr.contract"].create(
            {
                "name": "Contract",
                "employee_id": self.employee.id,
                "resource_calendar_id": self.calendar.id,
                "date_start": date(2024, 1, 1),
                "wage": 1,
            }
        )

    def _hours(self, day):
        self.env["calendar.public.holiday"].create(
            {"year": 2024, "line_ids": [(0, 0, {"date": day, "name": "Holiday"})]}
        )
        return self.env["hr.payslip"]._compute_public_holidays_days(
            self.contract, date(2024, 1, 1), date(2024, 1, 31)
        )["number_of_hours"]

    def test_a_weekday_holiday_counts_that_day_s_hours(self):
        self.assertEqual(self._hours(date(2024, 1, 2)), 9)  # Tuesday

    def test_a_saturday_holiday_counts_the_saturday_hours(self):
        self.assertEqual(self._hours(date(2024, 1, 6)), 4)

    def test_a_holiday_on_a_day_off_counts_an_average_day(self):
        # Sunday: nothing scheduled; the calendar's average day (49h / 6 days).
        self.assertAlmostEqual(self._hours(date(2024, 1, 7)), 49 / 6, places=2)

    def test_the_average_does_not_need_hours_per_day_to_be_filled(self):
        self.calendar.hours_per_day = 0
        self.assertAlmostEqual(self._hours(date(2024, 1, 7)), 49 / 6, places=2)
