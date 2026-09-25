# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from dateutil import relativedelta

from odoo import fields
from odoo.tests import common


class TestPayrollAccount(common.TransactionCase):
    def setUp(self):
        super().setUp()

        # Activate company currency
        self.env.user.company_id.currency_id.active = True

        # Ensure a default/base user exists for tests.
        # Ensure a simple default user exists and bind it to xmlid 'base.default_user'.
        IrModelData = self.env["ir.model.data"]
        try:
            self.env.ref("base.default_user")
        except ValueError:
            default_user = self.env["res.users"].create(
                {
                    "name": "Default User",
                    "login": "default",
                    "email": "default@example.com",
                }
            )
            IrModelData.create(
                {
                    "module": "base",
                    "name": "default_user",
                    "model": "res.users",
                    "res_id": default_user.id,
                    "noupdate": True,
                }
            )

        self.payslip_action_id = self.ref("payroll.hr_payslip_menu")

        partner = self.env["res.partner"].create({"name": "Partner 12"})
        bank = self.env["res.bank"].create({"name": "Test Bank"})
        self.res_partner_bank = self.env["res.partner.bank"].create(
            {
                "acc_number": "001-9876543-21",
                "partner_id": partner.id,
                "acc_type": "bank",
                "bank_id": bank.id,
            }
        )

        department = self.env["hr.department"].create({"name": "R&D"})
        self.hr_employee_john = self.env["hr.employee"].create(
            {
                "name": "John",
                "department_id": department.id,
            }
        )

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

        # Create minimal salary rules locally (avoid demo xmlids)
        self.hra_rule = self.env["hr.salary.rule"].create(
            {
                "name": "House Rent Allowance",
                "code": "HRA",
                "sequence": 5,
                "amount_select": "percentage",
                "amount_percentage": 40.0,
                "amount_percentage_base": "contract.wage",
            }
        )
        self.pf_rule = self.env["hr.salary.rule"].create(
            {
                "name": "Provident Fund",
                "code": "PF",
                "sequence": 150,
                "amount_select": "fix",
                "amount_fix": -200.0,
            }
        )
        rules = [self.hra_rule.id, self.pf_rule.id]
        self.hr_structure_softwaredeveloper = self.env["hr.payroll.structure"].create(
            {
                "name": "Salary Structure for Software Developer",
                "code": "SD",
                "rule_ids": [(6, 0, rules)],
            }
        )

        # Reuse the existing version created at employee creation to avoid
        # (employee_id, date_version) unique conflicts.
        self.hr_employee_john.version_id.write(
            {
                "contract_date_start": fields.Date.today(),
                "name": "Contract for John",
                "wage": 5000.0,
                "struct_id": self.hr_structure_softwaredeveloper.id,
                "journal_id": self.account_journal.id,
            }
        )
        self.hr_contract_john = self.hr_employee_john.version_id

    def _update_account_in_rule(self, debit, credit):
        # Update the HRA rule created in setUp
        self.hra_rule.write({"account_debit": debit, "account_credit": credit})

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
