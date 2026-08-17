# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase


class TestPayrollAttendanceReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
            }
        )
        cls.contract = cls.env["hr.contract"].create(
            {
                "name": "Contract",
                "employee_id": cls.employee.id,
                "date_start": datetime(2025, 1, 1),
                "wage": 1000,
                "state": "open",
            }
        )
        cls.date_from = datetime(2025, 1, 1)
        cls.date_to = datetime(2025, 1, 31)

        cls.payslip = cls.env["hr.payslip"].create(
            {
                "employee_id": cls.employee.id,
                "date_from": cls.date_from,
                "date_to": cls.date_to,
                "contract_id": cls.contract.id,
            }
        )
        cls.env["hr.attendance"].create(
            {
                "employee_id": cls.employee.id,
                "check_in": datetime(2025, 1, 10, 9, 0, 0),
                "check_out": datetime(2025, 1, 10, 17, 0, 0),
            }
        )
        cls.env["hr.attendance"].create(
            {
                "employee_id": cls.employee.id,
                "check_in": datetime(2025, 1, 15, 9, 0, 0),
                "check_out": datetime(2025, 1, 15, 13, 0, 0),
            }
        )

    def test_attendance_links_and_totals(self):
        self.payslip.compute_sheet()
        slip = self.payslip.with_context(prefetch_fields=False)
        self.assertTrue(hasattr(slip, "attendance_ids"))
        self.assertTrue(hasattr(slip, "total_worked_hours"))

        self.assertEqual(len(slip.attendance_ids), 2)

        self.assertAlmostEqual(slip.total_worked_hours, 12.0, places=2)

        for att in slip.attendance_ids:
            self.assertGreaterEqual(att.check_in, self.date_from)
            self.assertLessEqual(att.check_out, self.date_to + timedelta(days=1))
