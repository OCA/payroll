# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from dateutil import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form, common


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

    def _create_employee_without_journal(self, name):
        employee = self.env["hr.employee"].create({"name": name})
        employee.version_id.write(
            {
                "contract_date_start": fields.Date.today(),
                "name": f"Contract for {name}",
                "wage": 1000.0,
                "struct_id": self.hr_structure_softwaredeveloper.id,
            }
        )
        return employee

    def test_get_whitelist_fields_from_template_includes_journal(self):
        # journal_id must be copied from a contract template, like struct_id
        # and wage already are, otherwise a template's journal never reaches
        # the real contract created/updated from it.
        self.assertIn(
            "journal_id",
            self.env["hr.version"]._get_whitelist_fields_from_template(),
        )

    def test_create_journal_id_contract_priority_over_run_context(self):
        # The employee's own contract journal must win over the batch's
        # journal, even when the batch's journal is passed via context.
        run_journal = self.env["account.journal"].create(
            {"name": "Run Journal", "code": "RUNJ1", "type": "general"}
        )
        payslip = (
            self.env["hr.payslip"]
            .with_context(journal_id=run_journal.id)
            .create(
                {
                    "employee_id": self.hr_employee_john.id,
                    "contract_id": self.hr_contract_john.id,
                    "struct_id": self.hr_structure_softwaredeveloper.id,
                }
            )
        )
        self.assertEqual(payslip.journal_id, self.account_journal)

    def test_create_journal_id_falls_back_to_run_context(self):
        # When the contract has no journal of its own, the batch's journal
        # (passed via the 'journal_id' context key) is used instead.
        employee = self._create_employee_without_journal("No Journal Employee")
        run_journal = self.env["account.journal"].create(
            {"name": "Run Journal 2", "code": "RUNJ2", "type": "general"}
        )
        payslip = (
            self.env["hr.payslip"]
            .with_context(journal_id=run_journal.id)
            .create(
                {
                    "employee_id": employee.id,
                    "contract_id": employee.version_id.id,
                    "struct_id": self.hr_structure_softwaredeveloper.id,
                }
            )
        )
        self.assertEqual(payslip.journal_id, run_journal)

    def test_wizard_compute_sheet_uses_run_journal_as_fallback(self):
        employee = self._create_employee_without_journal("Wizard No Journal")
        run_journal = self.env["account.journal"].create(
            {"name": "Run Journal 3", "code": "RUNJ3", "type": "general"}
        )
        run = self.env["hr.payslip.run"].create(
            {
                "name": "Test Run Fallback",
                "journal_id": run_journal.id,
                "struct_id": self.hr_structure_softwaredeveloper.id,
            }
        )
        wizard = (
            self.env["hr.payslip.employees"]
            .with_context(active_id=run.id)
            .create({"employee_ids": [(6, 0, employee.ids)]})
        )
        wizard.compute_sheet()
        slip = self.env["hr.payslip"].search(
            [("employee_id", "=", employee.id), ("payslip_run_id", "=", run.id)]
        )
        self.assertEqual(slip.journal_id, run_journal)

    def test_wizard_compute_sheet_respects_contract_journal(self):
        run_journal = self.env["account.journal"].create(
            {"name": "Run Journal 4", "code": "RUNJ4", "type": "general"}
        )
        run = self.env["hr.payslip.run"].create(
            {
                "name": "Test Run Priority",
                "journal_id": run_journal.id,
                "struct_id": self.hr_structure_softwaredeveloper.id,
            }
        )
        wizard = (
            self.env["hr.payslip.employees"]
            .with_context(active_id=run.id)
            .create({"employee_ids": [(6, 0, self.hr_employee_john.ids)]})
        )
        wizard.compute_sheet()
        slip = self.env["hr.payslip"].search(
            [
                ("employee_id", "=", self.hr_employee_john.id),
                ("payslip_run_id", "=", run.id),
            ]
        )
        self.assertEqual(slip.journal_id, self.account_journal)

    def test_onchange_contract_sets_journal_from_contract(self):
        with Form(self.env["hr.payslip"]) as form:
            form.employee_id = self.hr_employee_john
            form.contract_id = self.hr_contract_john
        self.assertEqual(form.journal_id, self.account_journal)

    def _create_payslip_with_structure(self, structure):
        payslip = self.env["hr.payslip"].create(
            {
                "employee_id": self.hr_employee_john.id,
                "contract_id": self.hr_contract_john.id,
                "struct_id": structure.id,
                "journal_id": self.account_journal.id,
                "date_from": fields.Date.today().replace(day=1),
                "date_to": fields.Date.today(),
            }
        )
        payslip.compute_sheet()
        return payslip

    def test_action_payslip_done_creates_credit_adjustment_when_unbalanced(self):
        # Only a debit account configured: debit_sum > credit_sum, so an
        # automatic credit adjustment line must be added to balance the move.
        rule = self.env["hr.salary.rule"].create(
            {
                "name": "Debit Only",
                "code": "DEBONLY",
                "sequence": 10,
                "amount_select": "fix",
                "amount_fix": 100.0,
                "account_debit": self.account_debit.id,
            }
        )
        structure = self.env["hr.payroll.structure"].create(
            {
                "name": "Debit Only Structure",
                "code": "DOS",
                "rule_ids": [(6, 0, [rule.id])],
            }
        )
        self.hr_contract_john.struct_id = structure.id
        payslip = self._create_payslip_with_structure(structure)
        payslip.action_payslip_done()
        self.assertTrue(payslip.move_id)
        adjustment_lines = payslip.move_id.line_ids.filtered(
            lambda line: line.name == "Adjustment Entry"
        )
        self.assertTrue(adjustment_lines)
        self.assertAlmostEqual(
            sum(payslip.move_id.line_ids.mapped("debit")),
            sum(payslip.move_id.line_ids.mapped("credit")),
        )

    def test_action_payslip_done_creates_debit_adjustment_when_unbalanced(self):
        # Only a credit account configured: credit_sum > debit_sum, so an
        # automatic debit adjustment line must be added to balance the move.
        rule = self.env["hr.salary.rule"].create(
            {
                "name": "Credit Only",
                "code": "CREDONLY",
                "sequence": 10,
                "amount_select": "fix",
                "amount_fix": 100.0,
                "account_credit": self.account_credit.id,
            }
        )
        structure = self.env["hr.payroll.structure"].create(
            {
                "name": "Credit Only Structure",
                "code": "COS",
                "rule_ids": [(6, 0, [rule.id])],
            }
        )
        self.hr_contract_john.struct_id = structure.id
        payslip = self._create_payslip_with_structure(structure)
        payslip.action_payslip_done()
        self.assertTrue(payslip.move_id)
        adjustment_lines = payslip.move_id.line_ids.filtered(
            lambda line: line.name == "Adjustment Entry"
        )
        self.assertTrue(adjustment_lines)
        self.assertAlmostEqual(
            sum(payslip.move_id.line_ids.mapped("debit")),
            sum(payslip.move_id.line_ids.mapped("credit")),
        )

    def test_action_payslip_done_raises_without_default_account(self):
        # The credit-adjustment path must raise a clear UserError when the
        # journal has no default account to post the balancing line to.
        bad_journal = self.env["account.journal"].create(
            {"name": "No Default Account Journal", "code": "NODEF", "type": "general"}
        )
        rule = self.env["hr.salary.rule"].create(
            {
                "name": "Debit Only 2",
                "code": "DEBONLY2",
                "sequence": 10,
                "amount_select": "fix",
                "amount_fix": 100.0,
                "account_debit": self.account_debit.id,
            }
        )
        structure = self.env["hr.payroll.structure"].create(
            {
                "name": "Debit Only Structure 2",
                "code": "DOS2",
                "rule_ids": [(6, 0, [rule.id])],
            }
        )
        self.hr_contract_john.struct_id = structure.id
        payslip = self.env["hr.payslip"].create(
            {
                "employee_id": self.hr_employee_john.id,
                "contract_id": self.hr_contract_john.id,
                "struct_id": structure.id,
                "journal_id": bad_journal.id,
                "date_from": fields.Date.today().replace(day=1),
                "date_to": fields.Date.today(),
            }
        )
        payslip.compute_sheet()
        with self.assertRaises(UserError):
            payslip.action_payslip_done()

    def test_action_payslip_done_raises_without_default_account_debit_side(self):
        # Same as above but for the debit-adjustment path (credit-only rule).
        bad_journal = self.env["account.journal"].create(
            {
                "name": "No Default Account Journal 2",
                "code": "NODEF2",
                "type": "general",
            }
        )
        rule = self.env["hr.salary.rule"].create(
            {
                "name": "Credit Only 2",
                "code": "CREDONLY2",
                "sequence": 10,
                "amount_select": "fix",
                "amount_fix": 100.0,
                "account_credit": self.account_credit.id,
            }
        )
        structure = self.env["hr.payroll.structure"].create(
            {
                "name": "Credit Only Structure 2",
                "code": "COS2",
                "rule_ids": [(6, 0, [rule.id])],
            }
        )
        self.hr_contract_john.struct_id = structure.id
        payslip = self.env["hr.payslip"].create(
            {
                "employee_id": self.hr_employee_john.id,
                "contract_id": self.hr_contract_john.id,
                "struct_id": structure.id,
                "journal_id": bad_journal.id,
                "date_from": fields.Date.today().replace(day=1),
                "date_to": fields.Date.today(),
            }
        )
        payslip.compute_sheet()
        with self.assertRaises(UserError):
            payslip.action_payslip_done()

    def test_action_payslip_done_skips_zero_amount_lines(self):
        # A rule computing to a zero amount must not generate any move line.
        rule = self.env["hr.salary.rule"].create(
            {
                "name": "Zero Amount",
                "code": "ZERO",
                "sequence": 10,
                "amount_select": "fix",
                "amount_fix": 0.0,
                "account_debit": self.account_debit.id,
                "account_credit": self.account_credit.id,
            }
        )
        structure = self.env["hr.payroll.structure"].create(
            {
                "name": "Zero Amount Structure",
                "code": "ZAS",
                "rule_ids": [(6, 0, [rule.id])],
            }
        )
        self.hr_contract_john.struct_id = structure.id
        payslip = self._create_payslip_with_structure(structure)
        payslip.action_payslip_done()
        self.assertFalse(payslip.move_id)

    def test_action_payslip_done_uses_contract_analytic_account(self):
        # When the contract has its own analytic account, it takes priority
        # over the salary rule's analytic account on the generated move line.
        analytic_plan = self.env["account.analytic.plan"].search([], limit=1)
        contract_analytic = self.env["account.analytic.account"].create(
            {"name": "Contract Analytic", "plan_id": analytic_plan.id}
        )
        self.hr_contract_john.analytic_account_id = contract_analytic.id
        rule = self.env["hr.salary.rule"].create(
            {
                "name": "Analytic Rule",
                "code": "ANALYTIC",
                "sequence": 10,
                "amount_select": "fix",
                "amount_fix": 100.0,
                "account_debit": self.account_debit.id,
                "account_credit": self.account_credit.id,
            }
        )
        structure = self.env["hr.payroll.structure"].create(
            {
                "name": "Analytic Structure",
                "code": "ANS",
                "rule_ids": [(6, 0, [rule.id])],
            }
        )
        self.hr_contract_john.struct_id = structure.id
        payslip = self._create_payslip_with_structure(structure)
        payslip.action_payslip_done()
        distributions = payslip.move_id.line_ids.mapped("analytic_distribution")
        self.assertTrue(
            any(
                distribution and str(contract_analytic.id) in distribution
                for distribution in distributions
            )
        )

    def test_action_payslip_done_uses_salary_rule_analytic_account(self):
        # Without a contract analytic account, the salary rule's own analytic
        # account is used instead.
        analytic_plan = self.env["account.analytic.plan"].search([], limit=1)
        rule_analytic = self.env["account.analytic.account"].create(
            {"name": "Rule Analytic", "plan_id": analytic_plan.id}
        )
        rule = self.env["hr.salary.rule"].create(
            {
                "name": "Analytic Rule 2",
                "code": "ANALYTIC2",
                "sequence": 10,
                "amount_select": "fix",
                "amount_fix": 100.0,
                "account_debit": self.account_debit.id,
                "account_credit": self.account_credit.id,
                "analytic_account_id": rule_analytic.id,
            }
        )
        structure = self.env["hr.payroll.structure"].create(
            {
                "name": "Analytic Structure 2",
                "code": "ANS2",
                "rule_ids": [(6, 0, [rule.id])],
            }
        )
        self.hr_contract_john.struct_id = structure.id
        payslip = self._create_payslip_with_structure(structure)
        payslip.action_payslip_done()
        distributions = payslip.move_id.line_ids.mapped("analytic_distribution")
        self.assertTrue(
            any(
                distribution and str(rule_analytic.id) in distribution
                for distribution in distributions
            )
        )

    def test_action_payslip_cancel_reverses_move_when_hash_restricted(self):
        # On a hash-restricted journal, cancelling must reverse the move
        # instead of deleting it (deleting a hashed entry is not allowed).
        self._update_account_in_rule(self.account_debit, self.account_credit)
        payslip = self._prepare_payslip(self.hr_employee_john)
        payslip.compute_sheet()
        payslip.action_payslip_done()
        move = payslip.move_id
        move.journal_id.restrict_mode_hash_table = True
        self.env["ir.config_parameter"].sudo().set_param(
            "payroll.allow_cancel_payslips", "True"
        )
        payslip.action_payslip_cancel()
        self.assertFalse(payslip.move_id)
        self.assertTrue(
            move.exists(), "Hash-restricted move should be reversed, not deleted"
        )
