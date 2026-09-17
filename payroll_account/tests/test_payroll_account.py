# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from dateutil import relativedelta

from odoo import Command, fields
from odoo.tests import common


class TestPayrollAccount(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Activate company currency
        cls.env.user.company_id.currency_id.active = True

        cls.payslip_action_id = cls.env.ref("payroll.hr_payslip_menu").id

        cls.res_partner_bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": "001-9876543-21",
                "partner_id": cls.env.ref("base.res_partner_12").id,
                "acc_type": "bank",
                "bank_id": cls.env.ref("base.res_bank_1").id,
            }
        )

        cls.hr_employee_john = cls.env["hr.employee"].create(
            {
                "address_id": cls.env.ref("base.res_partner_address_27").id,
                "birthday": "1984-05-01",
                "children": 0.0,
                "country_id": cls.env.ref("base.in").id,
                "department_id": cls.env.ref("hr.dep_rd").id,
                "gender": "male",
                "marital": "single",
                "name": "John",
                "bank_account_id": cls.res_partner_bank.id,
            }
        )

        cls.account_debit = cls.env["account.account"].create(
            {
                "name": "Debit Account",
                "code": "334411",
                "account_type": "expense",
                "reconcile": True,
            }
        )
        cls.account_credit = cls.env["account.account"].create(
            {
                "name": "Credit Account",
                "code": "114433",
                "account_type": "expense",
                "reconcile": True,
            }
        )

        cls.account_journal = cls.env["account.journal"].create(
            {
                "name": "Vendor Bills - Test",
                "code": "TEXJ",
                "type": "purchase",
                "default_account_id": cls.account_debit.id,
                "refund_sequence": True,
            }
        )

        rules = [
            cls.env.ref("payroll.hr_salary_rule_houserentallowance1").id,
            cls.env.ref("payroll.hr_salary_rule_providentfund1").id,
        ]
        cls.hr_structure_softwaredeveloper = cls.env["hr.payroll.structure"].create(
            {
                "name": "Salary Structure for Software Developer",
                "code": "SD",
                "parent_id": cls.env.ref("payroll.structure_base").id,
                "rule_ids": [Command.set(rules)],
            }
        )

        cls.hr_contract_john = cls.env["hr.contract"].create(
            {
                "date_end": fields.Date.to_string(datetime.now() + timedelta(days=365)),
                "date_start": fields.Date.today(),
                "name": "Contract for John",
                "wage": 5000.0,
                "employee_id": cls.hr_employee_john.id,
                "struct_id": cls.hr_structure_softwaredeveloper.id,
                "journal_id": cls.account_journal.id,
            }
        )

    def _update_account_in_rule(self, debit, credit):
        rule_HRA = self.env.ref("payroll.hr_salary_rule_houserentallowance1")
        rule_HRA.write({"account_debit": debit, "account_credit": credit})

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
            Command.create(i) for i in res["value"]["worked_days_line_ids"]
        ]
        vals["input_line_ids"] = [
            Command.create(i) for i in res["value"]["input_line_ids"]
        ]
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
        rule = self.env.ref("payroll.hr_salary_rule_houserentallowance1")
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

    def test_partner_falls_back_to_the_bank_account_partner(self):
        """Without a work contact, the employee's bank account names the partner."""
        register_partner = self.env["res.partner"].create({"name": "Tax Authority"})
        register = self.env["hr.contribution.register"].create(
            {"name": "Tax Register", "partner_id": register_partner.id}
        )
        rule = self.env.ref("payroll.hr_salary_rule_houserentallowance1")
        rule.register_id = register
        payslip = self._prepare_payslip(self.hr_employee_john)
        line = self.env["hr.payslip.line"].create(
            {"slip_id": payslip.id, "salary_rule_id": rule.id, "name": "Test"}
        )
        self.hr_employee_john.work_contact_id = False
        self.account_credit.account_type = "asset_receivable"
        rule.account_credit = self.account_credit

        self.assertEqual(
            line._get_partner_id(True), self.res_partner_bank.partner_id.id
        )

    def test_accounting_entry_button_opens_the_move(self):
        self._update_account_in_rule(self.account_debit, self.account_credit)
        payslip = self._prepare_payslip(self.hr_employee_john)
        payslip.action_payslip_done()

        action = payslip.action_open_accounting_entry()

        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(action["res_id"], payslip.move_id.id)
