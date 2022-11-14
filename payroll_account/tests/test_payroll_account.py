# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from dateutil import relativedelta

from odoo import fields
from odoo.tests import common


class TestPayrollAccount(common.TransactionCase):
    def setUp(self):
        super(TestPayrollAccount, self).setUp()

        # Activate company currency
        self.env.user.company_id.currency_id.active = True

        self.payslip_action_id = self.ref("payroll.hr_payslip_menu")

        self.res_partner_bank = self.env["res.partner.bank"].create(
            {
                "acc_number": "001-9876543-21",
                "partner_id": self.ref("base.res_partner_12"),
                "acc_type": "bank",
                "bank_id": self.ref("base.res_bank_1"),
            }
        )

        self.hr_employee_john = self.env["hr.employee"].create(
            {
                "address_home_id": self.ref("base.res_partner_address_2"),
                "address_id": self.ref("base.res_partner_address_27"),
                "birthday": "1984-05-01",
                "children": 0.0,
                "country_id": self.ref("base.in"),
                "department_id": self.ref("hr.dep_rd"),
                "gender": "male",
                "marital": "single",
                "name": "John",
                "bank_account_id": self.res_partner_bank.bank_id.id,
            }
        )

        self.hr_salary_rule_houserentallowance1 = self.ref(
            "payroll.hr_salary_rule_houserentallowance1"
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

        self.hr_structure_softwaredeveloper = self.env["hr.payroll.structure"].create(
            {
                "name": "Salary Structure for Software Developer",
                "code": "SD",
                "company_id": self.ref("base.main_company"),
                "parent_id": self.ref("payroll.structure_base"),
                "rule_ids": [
                    (
                        6,
                        0,
                        [
                            self.ref("payroll.hr_salary_rule_houserentallowance1"),
                            self.ref("payroll.hr_salary_rule_convanceallowance1"),
                            self.ref("payroll.hr_salary_rule_professionaltax1"),
                            self.ref("payroll.hr_salary_rule_providentfund1"),
                            self.ref("payroll.hr_salary_rule_meal_voucher"),
                            self.ref("payroll.hr_salary_rule_sales_commission"),
                        ],
                    )
                ],
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

        self.hr_contract_john = self.env["hr.contract"].create(
            {
                "date_end": fields.Date.to_string(datetime.now() + timedelta(days=365)),
                "date_start": fields.Date.today(),
                "name": "Contract for John",
                "wage": 5000.0,
                "employee_id": self.hr_employee_john.id,
                "struct_id": self.hr_structure_softwaredeveloper.id,
                "journal_id": self.account_journal.id,
            }
        )

        self.hr_payslip = self.env["hr.payslip"].create(
            {
                "employee_id": self.hr_employee_john.id,
                "journal_id": self.account_journal.id,
            }
        )

    def _update_account_in_rule(self, debit, credit):
        rule_houserentallowance1 = self.env["hr.salary.rule"].browse(
            self.hr_salary_rule_houserentallowance1
        )
        rule_houserentallowance1.write(
            {"account_debit": debit, "account_credit": credit}
        )

    def test_00_hr_payslip(self):
        """checking the process of payslip."""

        date_from = datetime.now()
        date_to = datetime.now() + relativedelta.relativedelta(
            months=+1, day=1, days=-1
        )
        res = self.hr_payslip.get_payslip_vals(
            date_from, date_to, self.hr_employee_john.id
        )
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

        self._update_account_in_rule(self.account_debit, self.account_credit)
        self.hr_payslip.action_payslip_done()

        # I verify that the Accounting Entries are created.
        self.assertTrue(
            self.hr_payslip.move_id, "Accounting Entries has not been created"
        )

        # I verify that the payslip is in done state.
        self.assertEqual(self.hr_payslip.state, "done", "State not changed!")

    def test_hr_payslip_no_accounts(self):

        date_from = datetime.now()
        date_to = datetime.now() + relativedelta.relativedelta(
            months=+1, day=1, days=-1
        )
        res = self.hr_payslip.get_payslip_vals(
            date_from, date_to, self.hr_employee_john.id
        )
        vals = {
            "struct_id": res["value"]["struct_id"],
            "contract_id": self.hr_contract_john.id,
            "name": res["value"]["name"],
        }
        self.hr_payslip.write(vals)

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
