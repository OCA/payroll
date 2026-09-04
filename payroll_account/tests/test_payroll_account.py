# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from dateutil import relativedelta

from odoo import fields
from odoo.exceptions import UserError

from odoo.addons.payroll.tests.common import TestPayslipBase


class TestPayrollAccount(TestPayslipBase):
    def setUp(self):
        super().setUp()

        # Activate company currency
        self.env.user.company_id.currency_id.active = True

        self.payslip_action_id = self.ref("payroll.hr_payslip_menu")

        self.work_address = self.env["res.partner"].create(
            {"name": "John's Work Address"}
        )
        self.hr_employee_john = self.env["hr.employee"].create(
            {
                "address_id": self.work_address.id,
                "birthday": "1984-05-01",
                "children": 0,
                "country_id": self.ref("base.in"),
                "department_id": self.dept_rd.id,
                "sex": "male",
                "marital": "single",
                "name": "John",
            }
        )

        # The work contact is created together with the employee, and is the
        # only partner a bank account may be attached to.
        self.res_bank = self.env["res.bank"].create({"name": "Test Bank"})
        self.res_partner_bank = self.env["res.partner.bank"].create(
            {
                "acc_number": "001-9876543-21",
                "partner_id": self.hr_employee_john.work_contact_id.id,
                "acc_type": "bank",
                "bank_id": self.res_bank.id,
            }
        )
        self.hr_employee_john.bank_account_ids = [(4, self.res_partner_bank.id)]

        self.account_debit = self.env["account.account"].create(
            {
                "name": "Debit Account",
                "code": "334411",
                "account_type": "expense",
                "reconcile": True,
            }
        )
        self.account_credit = self.env["account.account"].create(
            {
                "name": "Credit Account",
                "code": "114433",
                "account_type": "expense",
                "reconcile": True,
            }
        )

        self.account_journal = self.env["account.journal"].create(
            {
                "name": "Vendor Bills - Test",
                "code": "TEXJ",
                "type": "purchase",
                "default_account_id": self.account_debit.id,
                "refund_sequence": True,
            }
        )

        self.analytic_plan = self.env["account.analytic.plan"].create(
            {"name": "Payroll Plan"}
        )
        self.analytic_account = self.env["account.analytic.account"].create(
            {"name": "Payroll Analytic", "plan_id": self.analytic_plan.id}
        )

        # Salary rules and structure come from payroll's test fixtures: since
        # 19.0 databases are initialized without demo data, the payroll demo
        # records are not available.
        self.hr_structure_softwaredeveloper = self.developer_pay_structure

        # Since 19.0 contracts are versions of the employee: complete the
        # version created along with the employee instead of creating one.
        self.hr_contract_john = self.hr_employee_john.version_id
        self.hr_contract_john.write(
            {
                "contract_date_start": fields.Date.today(),
                "contract_date_end": fields.Date.to_string(
                    datetime.now() + timedelta(days=365)
                ),
                "name": "Contract for John",
                "wage": 5000.0,
                "struct_id": self.hr_structure_softwaredeveloper.id,
                "journal_id": self.account_journal.id,
            }
        )

    def _update_account_in_rule(self, debit, credit):
        self.rule_hra.write({"account_debit": debit, "account_credit": credit})

    def _prepare_payslip(self, employee):
        date_from = datetime.now()
        date_to = datetime.now() + relativedelta.relativedelta(
            months=+1, day=1, days=-1
        )
        self.hr_payslip = self.env["hr.payslip"].create(
            {
                "employee_id": self.hr_employee_john.id,
                "contract_id": self.hr_contract_john.id,
                "struct_id": self.hr_structure_softwaredeveloper.id,
            }
        )
        res = self.hr_payslip.get_payslip_vals(date_from, date_to, employee.id)
        vals = {
            "struct_id": res["value"]["struct_id"],
            "contract_id": res["value"]["contract_id"],
            "name": res["value"]["name"],
        }
        vals["worked_days_line_ids"] = [
            (0, 0, i) for i in res["value"]["worked_days_line_ids"]
        ]
        vals["input_line_ids"] = [(0, 0, i) for i in res["value"]["input_line_ids"]]
        vals.update({"contract_id": self.hr_contract_john.id})
        self.hr_payslip.write(vals)
        return self.hr_payslip

    def test_00_hr_payslip(self):
        """checking the process of payslip."""
        self._update_account_in_rule(self.account_debit, self.account_credit)
        self._prepare_payslip(self.hr_employee_john)

        # I assign the amount to Input data.
        payslip_input = self.env["hr.payslip.input"].search(
            [("payslip_id", "=", self.hr_payslip.id)]
        )
        payslip_input.write({"amount": 5.0})

        # I verify the payslip is in draft state.
        self.assertEqual(self.hr_payslip.state, "draft", "State not changed!")

        # I click on "Compute Sheet" button.
        self.hr_payslip.with_context(
            {},
            lang="en_US",
            tz=False,
            active_model="hr.payslip",
            department_id=False,
            active_ids=[self.payslip_action_id],
            section_id=False,
            active_id=self.payslip_action_id,
        ).compute_sheet()

        # I want to check cancel button.
        # So I first cancel the sheet then make it set to draft.
        self.hr_payslip.action_payslip_cancel()
        self.assertEqual(self.hr_payslip.state, "cancel", "Payslip is rejected.")
        self.hr_payslip.action_payslip_draft()

        self.hr_payslip.action_payslip_done()

        # I verify that the Accounting Entries are created.
        self.assertTrue(self.hr_payslip.move_id, "Accounting Entries should be created")

        # I verify that the payslip is in done state.
        self.assertEqual(self.hr_payslip.state, "done", "State not changed!")

    def test_hr_payslip_no_accounts(self):
        self._prepare_payslip(self.hr_employee_john)

        # I click on "Compute Sheet" button.
        self.hr_payslip.with_context(
            {},
            lang="en_US",
            tz=False,
            active_model="hr.payslip",
            department_id=False,
            active_ids=[self.payslip_action_id],
            section_id=False,
            active_id=self.payslip_action_id,
        ).compute_sheet()

        # Confirm Payslip (no account moves)
        self.hr_payslip.action_payslip_done()
        self.assertFalse(self.hr_payslip.move_id, "Accounting Entries has been created")

        # I verify that the payslip is in done state.
        self.assertEqual(self.hr_payslip.state, "done", "State not changed!")

    def test_partner_logic_account_types(self):
        """Test partner logic for different account types."""
        # Employee already has work_contact_id auto-created
        employee_partner = self.hr_employee_john.work_contact_id

        # Create register with different partner
        register_partner = self.env["res.partner"].create({"name": "Tax Authority"})
        register = self.env["hr.contribution.register"].create(
            {"name": "Tax Register", "partner_id": register_partner.id}
        )

        # Create rule and payslip line
        rule = self.rule_hra
        rule.register_id = register
        payslip = self._prepare_payslip(self.hr_employee_john)
        line = self.env["hr.payslip.line"].create(
            {"slip_id": payslip.id, "salary_rule_id": rule.id, "name": "Test"}
        )

        # Test asset_receivable -> employee partner
        self.account_credit.account_type = "asset_receivable"
        rule.account_credit = self.account_credit
        self.assertEqual(line._get_partner_id(True), employee_partner.id)

        # Test liability_current -> employee partner
        self.account_credit.account_type = "liability_current"
        self.assertEqual(line._get_partner_id(True), employee_partner.id)

        # Test liability_payable -> register partner
        self.account_credit.account_type = "liability_payable"
        self.assertEqual(line._get_partner_id(True), register_partner.id)

        # Test other account types -> no partner
        self.account_credit.account_type = "expense"
        self.assertFalse(line._get_partner_id(True))

    def test_partner_logic_bank_account_fallback(self):
        """Without a work contact, the primary bank account partner is used."""
        payslip = self._prepare_payslip(self.hr_employee_john)
        rule = self.rule_hra
        line = self.env["hr.payslip.line"].create(
            {"slip_id": payslip.id, "salary_rule_id": rule.id, "name": "Test"}
        )
        bank_partner = self.res_partner_bank.partner_id
        self.hr_employee_john.work_contact_id = False

        self.account_credit.account_type = "asset_receivable"
        rule.account_credit = self.account_credit
        self.assertEqual(
            self.hr_employee_john.primary_bank_account_id, self.res_partner_bank
        )
        self.assertEqual(line._get_partner_id(True), bank_partner.id)

    def _confirm_payslip(self):
        """Compute and confirm the payslip of John, return its account move."""
        self._prepare_payslip(self.hr_employee_john)
        self.hr_payslip.compute_sheet()
        self.hr_payslip.action_payslip_done()
        return self.hr_payslip.move_id

    def _journal_without_default_account(self):
        journal = self.env["account.journal"].create(
            {"name": "No Default Account", "code": "NODEF", "type": "general"}
        )
        journal.default_account_id = False
        self.hr_contract_john.journal_id = journal
        return journal

    def test_contract_template_whitelist(self):
        """Accounting fields are propagated from a contract template."""
        whitelist = self.env["hr.version"]._get_whitelist_fields_from_template()
        self.assertIn("analytic_account_id", whitelist)
        self.assertIn("journal_id", whitelist)

        # a contract template is a version without employee
        template = self.env["hr.version"].create(
            {
                "name": "Template with accounting",
                "wage": 1000.0,
                "journal_id": self.account_journal.id,
                "analytic_account_id": self.analytic_account.id,
            }
        )
        values = self.env["hr.version"].get_values_from_contract_template(template)
        self.assertEqual(values["journal_id"], self.account_journal.id)
        self.assertEqual(values["analytic_account_id"], self.analytic_account.id)

    def test_onchange_contract_keeps_journal(self):
        """The journal follows the contract of the payslip."""
        self._prepare_payslip(self.hr_employee_john)
        self.hr_payslip.onchange_contract()
        self.assertEqual(self.hr_payslip.journal_id, self.account_journal)

    def test_payslip_run_wizard_uses_run_journal(self):
        """Payslips generated from a batch are created with its journal."""
        payslip_run = self.env["hr.payslip.run"].create(
            {"name": "Payslip Run", "journal_id": self.account_journal.id}
        )
        wizard = (
            self.env["hr.payslip.employees"]
            .with_context(active_id=payslip_run.id, active_model="hr.payslip.run")
            .create({"employee_ids": [(6, 0, self.hr_employee_john.ids)]})
        )
        wizard.compute_sheet()
        payslips = self.env["hr.payslip"].search(
            [("payslip_run_id", "=", payslip_run.id)]
        )
        self.assertEqual(payslips.employee_id, self.hr_employee_john)
        self.assertEqual(payslips.journal_id, self.account_journal)

    def test_analytic_distribution_from_contract(self):
        """The contract analytic account is set on the move lines."""
        self._update_account_in_rule(self.account_debit, self.account_credit)
        self.hr_contract_john.analytic_account_id = self.analytic_account
        move = self._confirm_payslip()
        self.assertTrue(move.line_ids)
        for line in move.line_ids:
            self.assertEqual(
                line.analytic_distribution, {str(self.analytic_account.id): 100}
            )

    def test_analytic_distribution_from_salary_rule(self):
        """Without one on the contract, the rule analytic account is used."""
        self._update_account_in_rule(self.account_debit, self.account_credit)
        self.assertFalse(self.hr_contract_john.analytic_account_id)
        self.rule_hra.analytic_account_id = self.analytic_account
        move = self._confirm_payslip()
        self.assertTrue(move.line_ids)
        for line in move.line_ids:
            self.assertEqual(
                line.analytic_distribution, {str(self.analytic_account.id): 100}
            )

    def test_adjustment_credit_line(self):
        """Debit only lines are balanced with an adjustment credit line."""
        self.rule_hra.write(
            {"account_debit": self.account_debit.id, "account_credit": False}
        )
        move = self._confirm_payslip()
        adjustment = move.line_ids.filtered(
            lambda line: line.name == "Adjustment Entry"
        )
        self.assertTrue(adjustment)
        self.assertTrue(adjustment.credit)
        self.assertFalse(adjustment.debit)
        self.assertEqual(adjustment.account_id, self.account_journal.default_account_id)

    def test_adjustment_debit_line(self):
        """Credit only lines are balanced with an adjustment debit line."""
        self.rule_hra.write(
            {"account_debit": False, "account_credit": self.account_credit.id}
        )
        move = self._confirm_payslip()
        adjustment = move.line_ids.filtered(
            lambda line: line.name == "Adjustment Entry"
        )
        self.assertTrue(adjustment)
        self.assertTrue(adjustment.debit)
        self.assertFalse(adjustment.credit)
        self.assertEqual(adjustment.account_id, self.account_journal.default_account_id)

    def test_adjustment_credit_without_journal_account(self):
        """A credit adjustment needs a default account on the journal."""
        self._journal_without_default_account()
        self.rule_hra.write(
            {"account_debit": self.account_debit.id, "account_credit": False}
        )
        self._prepare_payslip(self.hr_employee_john)
        self.hr_payslip.compute_sheet()
        with self.assertRaises(UserError):
            self.hr_payslip.action_payslip_done()

    def test_adjustment_debit_without_journal_account(self):
        """A debit adjustment needs a default account on the journal."""
        self._journal_without_default_account()
        self.rule_hra.write(
            {"account_debit": False, "account_credit": self.account_credit.id}
        )
        self._prepare_payslip(self.hr_employee_john)
        self.hr_payslip.compute_sheet()
        with self.assertRaises(UserError):
            self.hr_payslip.action_payslip_done()
