# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from dateutil import relativedelta

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import common


class TestPayrollAccount(common.TransactionCase):
    def setUp(self):
        super().setUp()

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

        rules = [
            self.ref("payroll.hr_salary_rule_houserentallowance1"),
            self.ref("payroll.hr_salary_rule_providentfund1"),
        ]
        self.hr_structure_softwaredeveloper = self.env["hr.payroll.structure"].create(
            {
                "name": "Salary Structure for Software Developer",
                "code": "SD",
                "parent_id": self.ref("payroll.structure_base"),
                "rule_ids": [(6, 0, rules)],
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

    # ------------------------------------------------------------------
    # Company consistency
    # ------------------------------------------------------------------
    def _other_company(self):
        company = self.env["res.company"].create({"name": "Payroll Other Company"})
        self.env.user.company_ids = [Command.link(company.id)]
        return company

    def test_accounts_are_read_in_the_payslip_company(self):
        """Debit/credit accounts are company-dependent.

        They must be resolved in the payslip's company, not in whatever
        company the confirming user happens to be working in.
        """
        self._update_account_in_rule(self.account_debit, self.account_credit)
        payslip = self._prepare_payslip(self.hr_employee_john)
        other_company = self._other_company()

        payslip.with_company(other_company).action_payslip_done()

        self.assertTrue(
            payslip.move_id,
            "The accounting entry must be generated with the accounts configured "
            "for the payslip's company",
        )
        accounts = payslip.move_id.line_ids.account_id
        self.assertIn(self.account_debit, accounts)
        self.assertIn(self.account_credit, accounts)

    def test_move_belongs_to_the_payslip_company(self):
        self._update_account_in_rule(self.account_debit, self.account_credit)
        payslip = self._prepare_payslip(self.hr_employee_john)
        other_company = self._other_company()

        payslip.with_company(other_company).action_payslip_done()

        move = payslip.move_id
        self.assertEqual(move.company_id, payslip.company_id)
        self.assertEqual(move.journal_id, payslip.journal_id)

    def test_move_is_balanced_posted_and_dated(self):
        self._update_account_in_rule(self.account_debit, self.account_credit)
        payslip = self._prepare_payslip(self.hr_employee_john)

        payslip.action_payslip_done()

        move = payslip.move_id
        self.assertEqual(move.state, "posted")
        self.assertEqual(move.ref, payslip.number)
        self.assertEqual(move.date, payslip.date)
        self.assertEqual(
            sum(move.line_ids.mapped("debit")),
            sum(move.line_ids.mapped("credit")),
            "The generated entry must be balanced",
        )

    def test_batch_default_journal_belongs_to_the_active_company(self):
        other_company = self._other_company()
        other_journal = self.env["account.journal"].create(
            {
                "name": "Salaries - Other Company",
                "code": "SALOC",
                "type": "general",
                "company_id": other_company.id,
            }
        )

        defaults = (
            self.env["hr.payslip.run"]
            .with_company(other_company)
            .default_get(["journal_id"])
        )

        self.assertEqual(defaults.get("journal_id"), other_journal.id)

    def test_tax_details_with_several_matching_repartition_lines(self):
        """A tax may spread over several repartition lines on the same account.

        Reading ``.id`` off that recordset raises, so the lookup has to be
        limited to one record.
        """
        tax = self.env["account.tax"].create(
            {
                "name": "Payroll Tax",
                "amount_type": "fixed",
                "amount": 0.0,
                "type_tax_use": "purchase",
                "invoice_repartition_line_ids": [
                    Command.create({"repartition_type": "base"}),
                    Command.create(
                        {
                            "repartition_type": "tax",
                            "factor_percent": 50.0,
                            "account_id": self.account_debit.id,
                        }
                    ),
                    Command.create(
                        {
                            "repartition_type": "tax",
                            "factor_percent": 50.0,
                            "account_id": self.account_debit.id,
                        }
                    ),
                ],
                "refund_repartition_line_ids": [
                    Command.create({"repartition_type": "base"}),
                    Command.create(
                        {
                            "repartition_type": "tax",
                            "factor_percent": 50.0,
                            "account_id": self.account_debit.id,
                        }
                    ),
                    Command.create(
                        {
                            "repartition_type": "tax",
                            "factor_percent": 50.0,
                            "account_id": self.account_debit.id,
                        }
                    ),
                ],
            }
        )
        rule = self.env.ref("payroll.hr_salary_rule_houserentallowance1")
        self._update_account_in_rule(self.account_debit, self.account_credit)
        rule.account_tax_id = tax
        payslip = self._prepare_payslip(self.hr_employee_john)
        line = self.env["hr.payslip.line"].create(
            {"slip_id": payslip.id, "salary_rule_id": rule.id, "name": "Test"}
        )

        _tax_ids, tax_tag_ids, tax_repartition_line_id = payslip._get_tax_details(line)

        self.assertIn(
            tax_repartition_line_id,
            tax.invoice_repartition_line_ids.ids,
            "A single invoice repartition line of the tax must be selected",
        )
        self.assertTrue(tax_tag_ids is False or isinstance(tax_tag_ids, list))

    # ------------------------------------------------------------------
    # Accounting entry life cycle
    # ------------------------------------------------------------------
    def _allow_cancelling_payslips(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "payroll.allow_cancel_payslips", True
        )

    def _confirmed_payslip(self):
        self._update_account_in_rule(self.account_debit, self.account_credit)
        payslip = self._prepare_payslip(self.hr_employee_john)
        payslip.action_payslip_done()
        self.assertTrue(payslip.move_id)
        return payslip

    def test_cancel_reverses_the_entry_instead_of_deleting_it(self):
        self._allow_cancelling_payslips()
        payslip = self._confirmed_payslip()
        move = payslip.move_id

        payslip.action_payslip_cancel()

        self.assertEqual(payslip.state, "cancel")
        self.assertTrue(move.exists(), "The posted entry must not be deleted")
        self.assertEqual(move.state, "posted")
        reversal = move.reversal_move_ids
        self.assertEqual(len(reversal), 1, "The entry must have been reversed")
        self.assertEqual(reversal.reversed_entry_id, move)
        self.assertEqual(
            sum(reversal.line_ids.mapped("balance")),
            -sum(move.line_ids.mapped("balance")),
        )
        self.assertIn(move, payslip.cancelled_move_ids)
        self.assertIn(reversal, payslip.cancelled_move_ids)
        self.assertFalse(payslip.move_id)

    def test_confirming_twice_does_not_create_a_second_entry(self):
        payslip = self._confirmed_payslip()
        move = payslip.move_id
        move_count = self.env["account.move"].search_count([])

        payslip.action_payslip_done()

        self.assertEqual(payslip.move_id, move)
        self.assertEqual(self.env["account.move"].search_count([]), move_count)

    def test_cancel_then_confirm_again_creates_a_new_entry(self):
        self._allow_cancelling_payslips()
        payslip = self._confirmed_payslip()
        first_move = payslip.move_id
        payslip.action_payslip_cancel()
        payslip.action_payslip_draft()

        payslip.action_payslip_done()

        self.assertTrue(payslip.move_id)
        self.assertNotEqual(payslip.move_id, first_move)

    def test_cannot_delete_a_payslip_with_a_posted_entry(self):
        payslip = self._confirmed_payslip()
        payslip.action_payslip_draft()

        with self.assertRaises(UserError):
            payslip.unlink()

    def test_cancel_deletes_an_entry_that_was_never_posted(self):
        self._allow_cancelling_payslips()
        payslip = self._confirmed_payslip()
        move = payslip.move_id
        move.button_draft()

        payslip.action_payslip_cancel()

        self.assertFalse(move.exists())
        self.assertFalse(payslip.move_id)

    # ------------------------------------------------------------------
    # Journal
    # ------------------------------------------------------------------
    def _new_journal(self, code="SALT2"):
        return self.env["account.journal"].create(
            {"name": f"Salaries {code}", "code": code, "type": "general"}
        )

    def _new_payslip(self, **vals):
        values = {
            "employee_id": self.hr_employee_john.id,
            "contract_id": self.hr_contract_john.id,
            "struct_id": self.hr_structure_softwaredeveloper.id,
            "name": "Payslip for John",
        }
        values.update(vals)
        return self.env["hr.payslip"].create(values)

    def test_journal_defaults_to_the_contract_journal(self):
        payslip = self._new_payslip()

        self.assertEqual(payslip.journal_id, self.account_journal)

    def test_journal_is_editable_on_a_single_payslip(self):
        self.assertFalse(
            self.env["hr.payslip"]._fields["journal_id"].readonly,
            "The form marks the journal as required, so it has to be editable",
        )
        payslip = self._new_payslip()
        other_journal = self._new_journal()

        payslip.journal_id = other_journal

        self.assertEqual(payslip.journal_id, other_journal)
        self.assertEqual(
            self.hr_contract_john.journal_id,
            self.account_journal,
            "Choosing a journal on one payslip must not touch the contract",
        )

    def test_changing_the_contract_journal_leaves_existing_payslips_alone(self):
        payslip = self._new_payslip()
        other_journal = self._new_journal(code="SALT3")

        self.hr_contract_john.journal_id = other_journal

        self.assertEqual(
            payslip.journal_id,
            self.account_journal,
            "An existing payslip must keep the journal it was created with",
        )

    def test_batch_journal_wins_over_the_contract_journal(self):
        batch_journal = self._new_journal(code="SALT4")
        payslip_run = self.env["hr.payslip.run"].create(
            {"name": "Batch", "journal_id": batch_journal.id}
        )

        payslip = self._new_payslip(payslip_run_id=payslip_run.id)

        self.assertEqual(payslip.journal_id, batch_journal)

    def test_default_journal_id_from_the_context_is_honoured(self):
        other_journal = self._new_journal(code="SALT5")

        payslip = (
            self.env["hr.payslip"]
            .with_context(default_journal_id=other_journal.id)
            .create(
                {
                    "employee_id": self.hr_employee_john.id,
                    "contract_id": self.hr_contract_john.id,
                    "struct_id": self.hr_structure_softwaredeveloper.id,
                    "name": "Payslip for John",
                }
            )
        )

        self.assertEqual(payslip.journal_id, other_journal)
