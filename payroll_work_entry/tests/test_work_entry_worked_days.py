# Copyright 2026 Anderson Oliveira
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import date

from odoo.tests import common

# Fixtures are built here on purpose: the OCA CI runs without demo data.


class TestWorkEntryWorkedDays(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Copy the company calendar: it carries real attendance lines. A bare
        # calendar makes every work entry fall "outside calendar" and Odoo 19
        # refuses to validate it.
        cls.calendar = cls.env.company.resource_calendar_id.copy(
            {"name": "Test Calendar"}
        )
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Work Entry Employee", "resource_calendar_id": cls.calendar.id}
        )
        cls.contract = cls.employee.version_id
        cls.contract.write(
            {
                "contract_date_start": date(2026, 1, 1),
                "name": "Test Contract",
                "wage": 3000.0,
                "resource_calendar_id": cls.calendar.id,
            }
        )

        cls.type_attendance = cls.env["hr.work.entry.type"].create(
            {"name": "Test Attendance", "code": "TESTWORK", "sequence": 10}
        )
        cls.type_overtime = cls.env["hr.work.entry.type"].create(
            {"name": "Test Overtime", "code": "TESTOT", "sequence": 20}
        )

        cls.category = cls.env["hr.salary.rule.category"].create(
            {"name": "Basic", "code": "BASIC"}
        )
        cls.rule = cls.env["hr.salary.rule"].create(
            {
                "name": "Overtime pay",
                "code": "OT_PAY",
                "sequence": 10,
                "category_id": cls.category.id,
                "condition_select": "none",
                "amount_select": "code",
                "amount_python_compute": (
                    "ot = worked_days.TESTOT\n"
                    "result = (ot.number_of_hours if ot else 0.0) * 50.0"
                ),
            }
        )
        cls.structure = cls.env["hr.payroll.structure"].create(
            {"name": "Test", "code": "TEST", "rule_ids": [(4, cls.rule.id)]}
        )
        cls.contract.struct_id = cls.structure

    def _work_entry(self, work_type, day, hours, state="validated"):
        entry = self.env["hr.work.entry"].create(
            {
                "name": f"{work_type.code} {day}",
                "employee_id": self.employee.id,
                "version_id": self.contract.id,
                "work_entry_type_id": work_type.id,
                "date": day,
                "duration": hours,
            }
        )
        if state == "validated":
            # Odoo 19 validates through action_validate(); writing the state
            # directly leaves it in conflict.
            entry.action_validate()
        else:
            entry.state = state
        return entry

    def _payslip(self):
        payslip = self.env["hr.payslip"].create(
            {
                "employee_id": self.employee.id,
                "contract_id": self.contract.id,
                "struct_id": self.structure.id,
                "date_from": date(2026, 3, 1),
                "date_to": date(2026, 3, 31),
                "name": "Test payslip",
            }
        )
        payslip.worked_days_line_ids = [
            (0, 0, line)
            for line in payslip.get_worked_day_lines(
                payslip._get_employee_contracts(), payslip.date_from, payslip.date_to
            )
        ]
        return payslip

    def _line(self, payslip, code):
        return payslip.worked_days_line_ids.filtered(lambda line: line.code == code)

    def test_worked_days_come_from_work_entries(self):
        """Hours are the ones actually recorded, not the calendar's."""
        for day in (2, 3, 4):
            self._work_entry(self.type_attendance, date(2026, 3, day), 8.0)

        payslip = self._payslip()
        line = self._line(payslip, "TESTWORK")

        self.assertTrue(line, "a TESTWORK line should have been produced")
        self.assertEqual(line.number_of_hours, 24.0)
        self.assertEqual(line.number_of_days, 3.0, "24h / 8h per day")

    def test_each_type_is_its_own_line(self):
        # Different days on purpose: Odoo 19 only validates one work entry per
        # employee and day, so a second one on the same date stays in conflict.
        self._work_entry(self.type_attendance, date(2026, 3, 2), 8.0)
        self._work_entry(self.type_overtime, date(2026, 3, 3), 2.0)

        payslip = self._payslip()

        self.assertEqual(len(payslip.worked_days_line_ids), 2)
        self.assertEqual(self._line(payslip, "TESTWORK").number_of_hours, 8.0)
        self.assertEqual(self._line(payslip, "TESTOT").number_of_hours, 2.0)

    def test_rule_reads_the_hours(self):
        """The whole point: a rule can pay the overtime that was recorded."""
        self._work_entry(self.type_attendance, date(2026, 3, 2), 8.0)
        self._work_entry(self.type_overtime, date(2026, 3, 3), 3.0)

        payslip = self._payslip()
        payslip.compute_sheet()

        line = payslip.line_ids.filtered(lambda line: line.code == "OT_PAY")
        self.assertEqual(line.total, 150.0, "3 recorded hours * 50")

    def test_only_validated_entries_count(self):
        self._work_entry(self.type_attendance, date(2026, 3, 2), 8.0)
        self._work_entry(self.type_attendance, date(2026, 3, 3), 8.0, state="draft")
        self._work_entry(self.type_attendance, date(2026, 3, 4), 8.0, state="cancelled")

        payslip = self._payslip()

        self.assertEqual(self._line(payslip, "TESTWORK").number_of_hours, 8.0)

    def test_entries_outside_the_period_are_ignored(self):
        self._work_entry(self.type_attendance, date(2026, 3, 2), 8.0)
        self._work_entry(self.type_attendance, date(2026, 2, 20), 8.0)
        self._work_entry(self.type_attendance, date(2026, 4, 5), 8.0)

        payslip = self._payslip()

        self.assertEqual(self._line(payslip, "TESTWORK").number_of_hours, 8.0)

    def test_days_follow_the_calendar_hours_per_day(self):
        """A 12-hour shift is not counted as if the day were 8 hours."""
        self.calendar.hours_per_day = 12.0
        self._work_entry(self.type_attendance, date(2026, 3, 2), 12.0)

        payslip = self._payslip()

        self.assertEqual(self._line(payslip, "TESTWORK").number_of_days, 1.0)

    def test_falls_back_to_the_calendar_without_work_entries(self):
        """Installing this module must not change payslips that have none."""
        payslip = self._payslip()

        self.assertTrue(
            payslip.worked_days_line_ids,
            "the calendar computation of payroll should still apply",
        )
