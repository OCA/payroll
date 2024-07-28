# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from dateutil import relativedelta

from odoo import fields
from odoo.tests import common


class TestPayrollAccount(common.TransactionCase):
    def setUp(self):
        super().setUp()

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

        # Additional setup for new tests
        self.hr_employee_jane = self.env["hr.employee"].create(
            {
                "name": "Jane",
                "gender": "female",
                "birthday": "1990-05-15",
                "department_id": self.ref("hr.dep_sales"),
            }
        )

        self.hr_contract_jane = self.env["hr.contract"].create(
            {
                "date_start": fields.Date.today(),
                "name": "Contract for Jane",
                "wage": 4000.0,
                "employee_id": self.hr_employee_jane.id,
                "struct_id": self.hr_structure_softwaredeveloper.id,
                "journal_id": self.account_journal.id,
            }
        )

        self.hr_salary_rule_houserentallowance1 = self.ref(
            "payroll.hr_salary_rule_houserentallowance1"
        )
        self.account_debit = self.env["account.account"].create(
            {
                "name": "Debit Account",
                "code": "334411",
                "user_type_id": self.env.ref("account.data_account_type_expenses").id,
                "reconcile": True,
            }
        )
        self.account_credit = self.env["account.account"].create(
            {
                "name": "Credit Account",
                "code": "114433",
                "user_type_id": self.env.ref("account.data_account_type_expenses").id,
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

        # Create a payslip run
        self.payslip_run = self.env["hr.payslip.run"].create(
            {
                "name": "Payslip Run",
                "date_start": fields.Date.today(),
                "date_end": fields.Date.today()
                + relativedelta.relativedelta(months=+1, day=1, days=-1),
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
        context = {
            "lang": "en_US",
            "tz": False,
            "active_model": "hr.payslip",
            "department_id": False,
            "active_ids": [self.payslip_action_id],
            "section_id": False,
            "active_id": self.payslip_action_id,
        }
        self.hr_payslip.with_context(context).compute_sheet()

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
        context = {
            "lang": "en_US",
            "tz": False,
            "active_model": "hr.payslip",
            "department_id": False,
            "active_ids": [self.payslip_action_id],
            "section_id": False,
            "active_id": self.payslip_action_id,
        }
        self.hr_payslip.with_context(context).compute_sheet()

        # Confirm Payslip (no account moves)
        self.hr_payslip.action_payslip_done()
        self.assertFalse(self.hr_payslip.move_id, "Accounting Entries has been created")

        # I verify that the payslip is in done state.
        self.assertEqual(self.hr_payslip.state, "done", "State not changed!")

    def test_payslip_run_accounting(self):
        """Test accounting entries for a payslip run (grouped payslips)."""
        # Create payslips for both employees
        payslip_john = self.create_payslip(self.hr_employee_john, self.payslip_run)
        payslip_jane = self.create_payslip(self.hr_employee_jane, self.payslip_run)

        # Compute payslips
        payslip_john.compute_sheet()
        payslip_jane.compute_sheet()

        # Confirm the payslip run
        self.payslip_run.action_validate()

        # Check that a single accounting entry was created for the run
        self.assertTrue(
            self.payslip_run.move_id, "No accounting entry created for payslip run"
        )
        self.assertEqual(
            payslip_john.move_id,
            self.payslip_run.move_id,
            "Incorrect move assigned to John's payslip",
        )
        self.assertEqual(
            payslip_jane.move_id,
            self.payslip_run.move_id,
            "Incorrect move assigned to Jane's payslip",
        )

        # Verify the contents of the accounting entry
        move_lines = self.payslip_run.move_id.line_ids
        self.assertTrue(len(move_lines) > 0, "No move lines created for payslip run")

        # Check that the move lines balance out to zero
        total_debit = sum(line.debit for line in move_lines)
        total_credit = sum(line.credit for line in move_lines)
        self.assertAlmostEqual(
            total_debit, total_credit, msg="Move lines do not balance for payslip run"
        )

    def test_different_salary_rules(self):
        """Test accounting entries for different types of salary rules."""
        # Create a new salary rule for a bonus
        bonus_rule = self.env["hr.salary.rule"].create(
            {
                "name": "Bonus",
                "code": "BONUS",
                "category_id": self.ref("payroll.ALW"),
                "sequence": 5,
                "amount_select": "fix",
                "amount_fix": 1000.0,
                "struct_id": self.hr_structure_softwaredeveloper.id,
                "account_debit": self.account_debit.id,
                "account_credit": self.account_credit.id,
            }
        )

        # Add the bonus rule to the structure
        self.hr_structure_softwaredeveloper.write({"rule_ids": [(4, bonus_rule.id)]})

        # Create and compute a payslip
        payslip = self.create_payslip(self.hr_employee_john)
        payslip.compute_sheet()

        # Confirm the payslip
        payslip.action_payslip_done()

        # Check that the bonus is reflected in the accounting entry
        bonus_line = payslip.move_id.line_ids.filtered(lambda l: l.name == "Bonus")
        self.assertTrue(bonus_line, "Bonus not reflected in accounting entry")
        self.assertEqual(
            bonus_line.debit, 1000.0, "Incorrect bonus amount in accounting entry"
        )

    def test_zero_amount_payslip(self):
        """Test payslip with zero amount."""
        # Modify the contract to have zero wage
        self.hr_contract_john.wage = 0.0

        # Create and compute a payslip
        payslip = self.create_payslip(self.hr_employee_john)
        payslip.compute_sheet()

        # Confirm the payslip
        payslip.action_payslip_done()

        # Check that no accounting entry was created
        self.assertFalse(
            payslip.move_id, "Accounting entry created for zero amount payslip"
        )

    def test_negative_amount_payslip(self):
        """Test payslip with negative amount."""
        # Create a negative salary rule (e.g., for recovery of overpayment)
        negative_rule = self.env["hr.salary.rule"].create(
            {
                "name": "Recovery",
                "code": "RECOV",
                "category_id": self.ref("payroll.DED"),
                "sequence": 100,
                "amount_select": "fix",
                "amount_fix": -500.0,
                "struct_id": self.hr_structure_softwaredeveloper.id,
                "account_debit": self.account_credit.id,  # Reversed for negative amount
                "account_credit": self.account_debit.id,  # Reversed for negative amount
            }
        )

        # Add the negative rule to the structure
        self.hr_structure_softwaredeveloper.write({"rule_ids": [(4, negative_rule.id)]})

        # Create and compute a payslip
        payslip = self.create_payslip(self.hr_employee_john)
        payslip.compute_sheet()

        # Confirm the payslip
        payslip.action_payslip_done()

        # Check that the negative amount is correctly reflected in the accounting entry
        recovery_line = payslip.move_id.line_ids.filtered(
            lambda l: l.name == "Recovery"
        )
        self.assertTrue(recovery_line, "Recovery not reflected in accounting entry")
        self.assertEqual(
            recovery_line.credit, 500.0, "Incorrect recovery amount in accounting entry"
        )

    def create_payslip(self, employee, payslip_run=None):
        """Helper method to create a payslip."""
        payslip = self.env["hr.payslip"].create(
            {
                "name": f"Payslip - {employee.name}",
                "employee_id": employee.id,
                "payslip_run_id": payslip_run and payslip_run.id or False,
                "date_from": fields.Date.today(),
                "date_to": fields.Date.today()
                + relativedelta.relativedelta(months=+1, day=1, days=-1),
                "contract_id": employee.contract_id.id,
                "struct_id": employee.contract_id.struct_id.id,
            }
        )
        return payslip
