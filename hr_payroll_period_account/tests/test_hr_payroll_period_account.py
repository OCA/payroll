# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from dateutil import relativedelta

from odoo import fields
from odoo.tests import common


class TestHrPayrollPeriodAccount(common.TransactionCase):
    """Tests for hr_payroll_period_account (payment_status and date_maturity)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.company_id.currency_id.active = True
        cls.company = cls.env.ref("base.main_company")

        # Bank and employee
        cls.res_partner_bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": "001-9876543-21",
                "partner_id": cls.env.ref("base.res_partner_12").id,
                "acc_type": "bank",
                "bank_id": cls.env.ref("base.res_bank_1").id,
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "address_home_id": cls.env.ref("base.res_partner_address_2").id,
                "address_id": cls.env.ref("base.res_partner_address_27").id,
                "birthday": "1984-05-01",
                "children": 0.0,
                "country_id": cls.env.ref("base.in").id,
                "department_id": cls.env.ref("hr.dep_rd").id,
                "gender": "male",
                "marital": "single",
                "name": "John",
                "bank_account_id": cls.res_partner_bank.bank_id.id,
            }
        )

        cls.account_expense = cls.env["account.account"].create(
            {
                "name": "Salary Expense",
                "code": "634400",
                "account_type": "expense",
                "reconcile": False,
            }
        )
        cls.account_payable = cls.env["account.account"].create(
            {
                "name": "Payable (Payroll)",
                "code": "220000",
                "account_type": "liability_payable",
                "reconcile": True,
            }
        )

        # Journal
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Payroll Journal Test",
                "code": "PAYJ",
                "type": "general",
                "default_account_id": cls.account_expense.id,
            }
        )

        # Salary rule: debit expense, credit payable (so we get a payable line to test)
        cls.rule = cls.env["hr.salary.rule"].browse(
            cls.env.ref("payroll.hr_salary_rule_houserentallowance1").id
        )
        cls.rule.write(
            {
                "account_debit": cls.account_expense.id,
                "account_credit": cls.account_payable.id,
            }
        )

        # Structure and contract
        cls.structure = cls.env["hr.payroll.structure"].create(
            {
                "name": "Test Structure",
                "code": "TS",
                "company_id": cls.company.id,
                "parent_id": cls.env.ref("payroll.structure_base").id,
                "rule_ids": [(6, 0, [cls.rule.id])],
            }
        )
        cls.contract = cls.env["hr.contract"].create(
            {
                "date_end": fields.Date.to_string(datetime.now() + timedelta(days=365)),
                "date_start": fields.Date.today(),
                "name": "Contract John",
                "wage": 5000.0,
                "employee_id": cls.employee.id,
                "struct_id": cls.structure.id,
                "journal_id": cls.journal.id,
            }
        )

    def _create_and_confirm_payslip(self, date_payment=None):
        date_from = datetime.now()
        date_to = datetime.now() + relativedelta.relativedelta(
            months=+1, day=1, days=-1
        )
        payslip = self.env["hr.payslip"].create(
            {
                "employee_id": self.employee.id,
                "contract_id": self.contract.id,
                "journal_id": self.journal.id,
            }
        )
        res = payslip.get_payslip_vals(date_from, date_to, self.employee.id)
        vals = {
            "struct_id": res["value"]["struct_id"],
            "contract_id": self.contract.id,
            "name": res["value"]["name"],
            "date_from": res["value"].get("date_from", date_from),
            "date_to": res["value"].get("date_to", date_to),
            "date_payment": date_payment
            or (date_to.date() if hasattr(date_to, "date") else date_to),
            "worked_days_line_ids": [
                (0, 0, i) for i in res["value"]["worked_days_line_ids"]
            ],
            "input_line_ids": [(0, 0, i) for i in res["value"]["input_line_ids"]],
        }
        payslip.write(vals)
        payslip.with_context(
            active_model="hr.payslip",
            active_ids=payslip.ids,
            active_id=payslip.id,
        ).compute_sheet()
        payslip.action_payslip_done()
        return payslip

    def test_payment_status_no_move(self):
        """Payslip without accounting move has payment_status False."""
        date_from = datetime.now()
        date_to = datetime.now() + relativedelta.relativedelta(
            months=+1, day=1, days=-1
        )
        payslip = self.env["hr.payslip"].create(
            {
                "employee_id": self.employee.id,
                "contract_id": self.contract.id,
                "journal_id": self.journal.id,
                "date_from": date_from,
                "date_to": date_to,
                "date_payment": date_to.date(),
            }
        )
        self.assertFalse(payslip.move_id)
        self.assertFalse(payslip.payment_status)

    def test_payment_status_no_payable_receivable_lines(self):
        """When move has no payable/receivable lines, payment_status is False."""
        # Use rule with both accounts expense so no payable line
        self.rule.write(
            {
                "account_debit": self.account_expense.id,
                "account_credit": self.account_expense.id,
            }
        )
        payslip = self._create_and_confirm_payslip()
        self.assertTrue(payslip.move_id)
        payable_receivable = payslip.move_id.line_ids.filtered(
            lambda line: line.account_id.account_type
            in ("asset_receivable", "liability_payable")
        )
        self.assertFalse(payable_receivable)
        self.assertFalse(payslip.payment_status)
        # Restore for other tests
        self.rule.write({"account_credit": self.account_payable.id})

    def test_payment_status_not_paid(self):
        """When move has unreconciled payable/receivable lines,
        payment_status is not_paid."""
        payslip = self._create_and_confirm_payslip()
        self.assertTrue(payslip.move_id)
        payable_lines = payslip.move_id.line_ids.filtered(
            lambda line: line.account_id.account_type == "liability_payable"
        )
        self.assertTrue(payable_lines, "Move should have a payable line")
        self.assertEqual(payslip.payment_status, "not_paid")

    def test_date_maturity_on_payable_lines(self):
        """date_payment is written to date_maturity on payable/receivable move lines."""
        date_payment = fields.Date.from_string("2026-02-15")
        payslip = self._create_and_confirm_payslip(date_payment=date_payment)
        payable_lines = payslip.move_id.line_ids.filtered(
            lambda line: line.account_id.account_type == "liability_payable"
        )
        self.assertTrue(payable_lines)
        for line in payable_lines:
            self.assertEqual(
                line.date_maturity,
                date_payment,
                "Payable line date_maturity should equal payslip date_payment",
            )

    def test_payment_status_paid_after_reconcile(self):
        """When all payable/receivable lines are reconciled, payment_status is paid."""
        payslip = self._create_and_confirm_payslip()
        # Only consider lines on the custom payroll payable account to avoid
        # mixing with other payable accounts that may appear on the move.
        payable_lines = payslip.move_id.line_ids.filtered(
            lambda line: line.account_id == self.account_payable
        )
        self.assertTrue(payable_lines)
        # Create counterpart move: debit same payable account, same partner, same amount
        partner = payable_lines[0].partner_id
        amount = sum(payable_lines.mapped("credit")) - sum(
            payable_lines.mapped("debit")
        )
        if amount <= 0:
            amount = abs(amount)
        counterpart_move = self.env["account.move"].create(
            {
                "journal_id": self.journal.id,
                "date": fields.Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Payable debit",
                            "account_id": self.account_payable.id,
                            "partner_id": partner.id,
                            "debit": amount,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Bank",
                            "account_id": self.journal.default_account_id.id,
                            "debit": 0.0,
                            "credit": amount,
                        },
                    ),
                ],
            }
        )
        counterpart_move.action_post()
        # Reconcile: lines to reconcile = payable lines from payslip + counterpart line
        to_reconcile = payable_lines | counterpart_move.line_ids.filtered(
            lambda line: line.account_id == self.account_payable
        )
        to_reconcile.reconcile()
        # Refresh and check
        payslip.invalidate_recordset()
        self.assertEqual(payslip.payment_status, "paid")
