# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.fields import Date

from .common import TestPayslipBase


class TestHrContractOpening(TestPayslipBase):
    def setUp(self):
        super().setUp()
        self.employee = self.env["hr.employee"].create({"name": "Test Employee"})
        self.contract = self.Contract.create(
            {
                "name": "Test Contract",
                "employee_id": self.employee.id,
                "wage": 200000.0,
                "state": "open",
                "date_start": Date.from_string("2026-01-01"),
            }
        )

    def test_opening_fields_default(self):
        """Opening fields are empty by default and contract has no payslips."""
        self.assertFalse(self.contract.opening_date)
        self.assertFalse(self.contract.seniority_date)
        self.assertEqual(self.contract.opening_leave_base, 0.0)
        self.assertEqual(self.contract.opening_leave_days, 0.0)
        self.assertEqual(self.contract.payslip_count, 0)

    def test_opening_fields_writable(self):
        """Opening fields can be written when no payslip exists."""
        self.contract.write(
            {
                "opening_date": Date.from_string("2026-05-31"),
                "seniority_date": Date.from_string("2018-03-15"),
                "opening_leave_base": 1200000.0,
                "opening_leave_days": 12.5,
            }
        )
        self.assertEqual(self.contract.opening_date, Date.from_string("2026-05-31"))
        self.assertEqual(
            self.contract.seniority_date,
            Date.from_string("2018-03-15"),
        )
        self.assertEqual(self.contract.opening_leave_base, 1200000.0)
        self.assertEqual(self.contract.opening_leave_days, 12.5)

    def test_payslip_count(self):
        """payslip_count reflects the number of payslips for the contract."""
        self.assertEqual(self.contract.payslip_count, 0)
        self.Payslip.create(
            {
                "name": "Test Payslip",
                "employee_id": self.employee.id,
                "contract_id": self.contract.id,
                "date_from": Date.from_string("2026-06-01"),
                "date_to": Date.from_string("2026-06-30"),
            }
        )
        self.assertEqual(self.contract.payslip_count, 1)
