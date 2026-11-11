# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from datetime import date, datetime

from odoo.exceptions import AccessError
from odoo.tests import Form, new_test_user

from .common import TestPayslipBase


class TestEmploymentWorkedPeriod(TestPayslipBase):
    def _period(self, hire, end=False, night=False):
        slots = [(0, 6), (22, 24)] if night else [(8, 16)]
        calendar = self.ResourceCalendar.create(
            {
                "name": "Employment period Mon-Fri8h",
                "tz": "Europe/Bratislava" if night else "UTC",
                "attendance_ids": [(5, 0, 0)]
                + [
                    (
                        0,
                        0,
                        {
                            "name": str(day),
                            "dayofweek": str(day),
                            "hour_from": start,
                            "hour_to": stop,
                            "day_period": "afternoon" if start == 22 else "morning",
                        },
                    )
                    for day in range(5)
                    for start, stop in slots
                ],
            }
        )
        employee = self.env["hr.employee"].create(
            {
                "name": "Employment boundary worker",
                "resource_calendar_id": calendar.id,
            }
        )
        version = employee.version_id
        version.write(
            {
                "date_version": hire,
                "contract_date_start": hire,
                "contract_date_end": end,
                "resource_calendar_id": calendar.id,
            }
        )
        self.period_version = version
        return self.Payslip.get_worked_day_lines(
            version, date(2027, 3, 1), date(2027, 3, 31)
        )

    def _normal_hours(self, rows):
        return sum(row["number_of_hours"] for row in rows if row["code"] == "WORK100")

    def test_worked_time_stops_at_employment_end(self):
        rows = self._period(date(2027, 1, 1), date(2027, 3, 15))
        self.assertEqual(self._normal_hours(rows), 88)

    def test_hire_and_end_in_the_same_month(self):
        rows = self._period(date(2027, 3, 10), date(2027, 3, 20))
        self.assertEqual(self._normal_hours(rows), 64)

    def test_open_employment_keeps_its_hire_boundary(self):
        rows = self._period(date(2027, 3, 16))
        self.assertEqual(self._normal_hours(rows), 96)

    def test_employment_outside_the_month_has_explicit_zero_time(self):
        for hire, end in (
            (date(2027, 1, 1), date(2027, 2, 28)),
            (date(2027, 4, 1), False),
        ):
            rows = self._period(hire, end)
            normal = [row for row in rows if row["code"] == "WORK100"]
            self.assertEqual(len(normal), 1)
            self.assertEqual(normal[0]["number_of_hours"], 0)
            self.assertEqual(normal[0]["number_of_days"], 0)

    def test_calendar_local_midnight_and_dst_month(self):
        for hire, end, expected in (
            (date(2027, 1, 1), False, 184),
            (date(2027, 3, 10), date(2027, 3, 20), 64),
        ):
            rows = self._period(hire, end, night=True)
            self.assertAlmostEqual(self._normal_hours(rows), expected, places=6)

    def test_payroll_officer_can_read_worked_period(self):
        self._period(date(2027, 1, 1), date(2027, 3, 15))
        officer = new_test_user(
            self.env,
            login="employment-period-officer",
            groups="base.group_user,hr.group_hr_user,payroll.group_payroll_user",
        )
        rows = self.Payslip.with_user(officer).get_worked_day_lines(
            self.period_version.with_user(officer), date(2027, 3, 1), date(2027, 3, 31)
        )
        self.assertEqual(self._normal_hours(rows), 88)
        outsider = new_test_user(
            self.env, login="employment-period-outsider", groups="base.group_user"
        )
        with self.assertRaises(AccessError):
            self.Payslip.with_user(outsider).get_worked_day_lines(
                self.period_version.with_user(outsider),
                date(2027, 3, 1),
                date(2027, 3, 31),
            )

    def test_next_version_ends_the_previous_worked_interval(self):
        self._period(date(2027, 1, 1))
        previous = self.period_version
        following = previous.copy({"date_version": date(2027, 3, 16)})
        previous.invalidate_recordset(["date_end"])
        self.assertEqual(previous.date_end, date(2027, 3, 15))
        rows = self.Payslip.get_worked_day_lines(
            previous | following, date(2027, 3, 1), date(2027, 3, 31)
        )
        self.assertEqual(
            [row["number_of_hours"] for row in rows if row["code"] == "WORK100"],
            [88, 96],
        )

    def test_leave_after_employment_end_is_excluded(self):
        self._period(date(2027, 1, 1), date(2027, 3, 15))
        version = self.period_version
        leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Employment boundary leave",
                "requires_allocation": False,
                "leave_validation_type": "no_validation",
            }
        )
        for day in (12, 16):
            leave = self.env["hr.leave"].create(
                {
                    "employee_id": version.employee_id.id,
                    "holiday_status_id": leave_type.id,
                    "request_date_from": date(2027, 3, day),
                    "request_date_to": date(2027, 3, day),
                }
            )
            if leave.state != "validate":
                leave.action_validate()
        rows = self.Payslip.get_worked_day_lines(
            version, date(2027, 3, 1), date(2027, 3, 31)
        )
        self.assertEqual(
            sum(
                abs(row["number_of_hours"]) for row in rows if row["code"] != "WORK100"
            ),
            8,
        )


class TestWorkedDays(TestPayslipBase):
    def setUp(self):
        super().setUp()

        self.LeaveRequest = self.env["hr.leave"]
        self.LeaveType = self.env["hr.leave.type"]

        # create holiday type
        self.holiday_type = self.LeaveType.create(
            {
                "name": "TestLeaveType",
                "allocation_validation_type": "no_validation",
                "leave_validation_type": "no_validation",
            }
        )

        self.full_calendar = self.ResourceCalendar.create(
            {
                "name": "56 Hrs a week",
                "tz": "UTC",
            }
        )
        # Create a full 7-day week sor our tests don't fail on Sat. and Sun.
        for day in ["0", "1", "2", "3", "4", "5", "6"]:
            self.CalendarAttendance.create(
                {
                    "calendar_id": self.full_calendar.id,
                    "dayofweek": day,
                    "name": "Morning",
                    "day_period": "morning",
                    "hour_from": 8,
                    "hour_to": 12,
                }
            )
            self.CalendarAttendance.create(
                {
                    "calendar_id": self.full_calendar.id,
                    "dayofweek": day,
                    "name": "Afternoon",
                    "day_period": "afternoon",
                    "hour_from": 13,
                    "hour_to": 17,
                }
            )

    def _common_contract_leave_setup(self):
        self.richard_emp.resource_id.calendar_id = self.full_calendar
        self.richard_emp.version_ids.resource_calendar_id = self.full_calendar

        # I put all eligible contracts (including Richard's) in an "open" state
        self.apply_contract_cron()

        self.env["hr.leave.allocation"].create(
            {
                "name": "Annual Time Off",
                "employee_id": self.richard_emp.id,
                "holiday_status_id": self.holiday_type.id,
                "number_of_days": 20,
                "state": "confirm",
                "date_from": time.strftime("%Y-01-01"),
                "date_to": time.strftime("%Y-12-31"),
            }
        )

        # Create the leave
        self.LeaveRequest.create(
            {
                "name": "Hol11",
                "employee_id": self.richard_emp.id,
                "holiday_status_id": self.holiday_type.id,
                "date_from": datetime.combine(date.today(), datetime.min.time()),
                "date_to": datetime.combine(date.today(), datetime.max.time()),
                "number_of_days": 1,
            }
        )

    def test_worked_days_negative(self):
        self._common_contract_leave_setup()

        # Set system parameter
        self.env["ir.config_parameter"].sudo().set_param(
            "payroll.leaves_positive", False
        )

        # I create an employee Payslip
        frm = Form(self.Payslip)
        frm.employee_id = self.richard_emp
        richard_payslip = frm.save()

        worked_days_codes = richard_payslip.worked_days_line_ids.mapped("code")
        self.assertIn(
            "GLOBAL", worked_days_codes, "The leave is in the 'Worked Days' list"
        )
        wdl_ids = richard_payslip.worked_days_line_ids.filtered(
            lambda x: x.code == "GLOBAL"
        )
        self.assertEqual(len(wdl_ids), 1, "There is only one line matching the leave")
        self.assertEqual(
            wdl_ids[0].number_of_days,
            -1.0,
            "The days worked value is a NEGATIVE number",
        )
        self.assertEqual(
            wdl_ids[0].number_of_hours,
            -8.0,
            "The hours worked value is a NEGATIVE number",
        )

    def test_leaves_positive(self):
        self._common_contract_leave_setup()

        # Set system parameter
        self.env["ir.config_parameter"].sudo().set_param(
            "payroll.leaves_positive", True
        )

        # I create an employee Payslip
        frm = Form(self.Payslip)
        frm.employee_id = self.richard_emp
        richard_payslip = frm.save()

        worked_days_codes = richard_payslip.worked_days_line_ids.mapped("code")
        self.assertIn(
            "GLOBAL", worked_days_codes, "The leave is in the 'Worked Days' list"
        )
        wdl_ids = richard_payslip.worked_days_line_ids.filtered(
            lambda x: x.code == "GLOBAL"
        )
        self.assertEqual(len(wdl_ids), 1, "There is only one line matching the leave")
        self.assertEqual(
            wdl_ids[0].number_of_days, 1.0, "The days worked value is a POSITIVE number"
        )
        self.assertEqual(
            wdl_ids[0].number_of_hours,
            8.0,
            "The hours worked value is a POSITIVE number",
        )
