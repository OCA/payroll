# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from datetime import timedelta

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, ValidationError
from odoo.tools import mute_logger

from odoo.addons.payroll.tests.common import TestPayslipBase


class TestSalaryRuleTagCommon(TestPayslipBase):
    def setUp(self):
        super().setUp()

        self.Tag = self.env["hr.salary.rule.tag"]
        self.tag_fixed = self.Tag.create({"name": "FixedPay"})
        self.tag_taxable = self.Tag.create({"name": "Taxable"})
        self.rule_basic.tag_ids = self.tag_fixed | self.tag_taxable
        self.rule_commission.tag_ids = self.tag_taxable

        self.rule_fixed = self.SalaryRule.create(
            {
                "name": "Fixed Pay Total",
                "code": "FIXED_TOTAL",
                "sequence": 20,
                "amount_select": "code",
                "amount_python_compute": "result = tags.FIXEDPAY",
            }
        )
        self.rule_taxable = self.SalaryRule.create(
            {
                "name": "Taxable Total",
                "code": "TAXABLE_TOTAL",
                "sequence": 21,
                "amount_select": "code",
                "amount_python_compute": "result = tags.TAXABLE",
            }
        )
        self.developer_pay_structure.rule_ids |= self.rule_fixed | self.rule_taxable

    def _create_payslip(self):
        # Anchor the period to the contract's own start date instead of
        # relying on the payslip's "current calendar month" default: the
        # contract starts on Date.today() (see TestPayslipBase.setUp), and
        # get_worked_day_lines() clamps date_from to the contract start, so
        # a default period would collapse to a single day whenever the
        # tests happen to run on the last day of the month -- making
        # WORK100.number_of_days == 1 and any "total != amount" assertion
        # on a per-worked-day rule fail by coincidence of the calendar.
        date_from = self.richard_contract.date_start
        payslip = self.Payslip.create(
            {
                "employee_id": self.richard_emp.id,
                "contract_id": self.richard_contract.id,
                "date_from": date_from,
                "date_to": date_from + timedelta(days=13),
            }
        )
        payslip.onchange_employee()
        return payslip

    def _get_amount(self, payslip, code):
        line = payslip.line_ids.filtered(lambda record: record.code == code)
        return line.amount

    def _get_total(self, payslip, code):
        """Line total, i.e. quantity * rate * amount, which is what tags sum."""
        line = payslip.line_ids.filtered(lambda record: record.code == code)
        return line.total


class TestSalaryRuleTag(TestSalaryRuleTagCommon):
    """Tag definition: defaults, code resolution and constraints."""

    def test_default_values(self):
        tag = self.Tag.create({"name": "Benefits"})
        self.assertTrue(tag.active)
        self.assertEqual(tag.sequence, 10)
        self.assertEqual(tag.company_id, self.env.company)

    def test_code_defaults_to_normalized_name(self):
        self.assertEqual(self.tag_taxable.get_tag_code(), "TAXABLE")
        self.assertEqual(
            self.Tag.create({"name": "Gross Pay"}).get_tag_code(), "GROSS_PAY"
        )
        self.assertEqual(
            self.Tag.create({"name": "Health (50%)"}).get_tag_code(), "HEALTH__50__"
        )

    def test_explicit_code_wins_over_name(self):
        tag = self.Tag.create({"name": "Taxable Base", "code": "TAXBASE"})
        self.assertEqual(tag.get_tag_code(), "TAXBASE")

    def test_code_does_not_depend_on_user_language(self):
        """A translated name must not change the code salary rules address."""
        self.env["res.lang"]._activate_lang("fr_FR")
        self.tag_taxable.with_context(lang="fr_FR").name = "Imposable"
        self.assertEqual(self.tag_taxable.with_context(lang="fr_FR").name, "Imposable")
        self.assertEqual(
            self.tag_taxable.with_context(lang="fr_FR").get_tag_code(), "TAXABLE"
        )

    def test_name_not_convertible_to_identifier_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.Tag.create({"name": "1st Bracket"})

    def test_invalid_code_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.Tag.create({"name": "Union Fee", "code": "union-fee"})

    def test_two_names_normalizing_to_one_code_are_rejected(self):
        self.Tag.create({"name": "Net Pay"})
        with self.assertRaises(ValidationError):
            self.Tag.create({"name": "Net-Pay"})

    def test_code_colliding_with_another_name_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.Tag.create({"name": "Income Tax", "code": "TAXABLE"})

    def test_archived_tag_still_reserves_its_code(self):
        self.tag_taxable.active = False
        with self.assertRaises(ValidationError):
            self.Tag.create({"name": "Taxable Amount", "code": "TAXABLE"})

    def test_same_code_allowed_in_another_company(self):
        other_company = self.env["res.company"].create({"name": "Second Company"})
        tag = self.Tag.create({"name": "Taxable", "company_id": other_company.id})
        self.assertEqual(tag.get_tag_code(), "TAXABLE")

    @mute_logger("odoo.sql_db")
    def test_duplicate_name_in_same_company_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.Tag.create({"name": "Taxable"})


class TestSalaryRuleTagRelation(TestSalaryRuleTagCommon):
    """Both sides of the rule/tag relation must stay in sync."""

    def test_tagging_a_rule_fills_the_tag_rules(self):
        self.assertIn(self.rule_basic, self.tag_taxable.salary_rules_ids)
        self.assertIn(self.rule_commission, self.tag_taxable.salary_rules_ids)
        self.assertNotIn(self.rule_commission, self.tag_fixed.salary_rules_ids)

    def test_rules_count_follows_the_relation(self):
        self.assertEqual(self.tag_taxable.salary_rules_count, 2)
        self.assertEqual(self.tag_fixed.salary_rules_count, 1)
        self.rule_commission.tag_ids -= self.tag_taxable
        self.assertEqual(self.tag_taxable.salary_rules_count, 1)

    def test_setting_rules_from_the_tag_tags_the_rule(self):
        self.tag_fixed.salary_rules_ids |= self.rule_hra
        self.assertIn(self.tag_fixed, self.rule_hra.tag_ids)


class TestSalaryRuleTagPayslip(TestSalaryRuleTagCommon):
    """Tag totals as exposed to salary rule computations."""

    def test_tag_totals_sum_their_rules(self):
        payslip = self._create_payslip()
        payslip.compute_sheet()

        basic = self._get_amount(payslip, "BASIC")
        commission = self._get_amount(payslip, "SALE")

        self.assertEqual(self._get_amount(payslip, "FIXED_TOTAL"), basic)
        self.assertEqual(self._get_amount(payslip, "TAXABLE_TOTAL"), basic + commission)

    def test_unknown_tag_total_is_zero(self):
        rule = self.SalaryRule.create(
            {
                "name": "Unused Tag Total",
                "code": "UNUSED_TOTAL",
                "sequence": 22,
                "amount_select": "code",
                "amount_python_compute": "result = tags.NOT_A_TAG",
            }
        )
        self.developer_pay_structure.rule_ids |= rule

        payslip = self._create_payslip()
        payslip.compute_sheet()

        self.assertEqual(self._get_amount(payslip, "UNUSED_TOTAL"), 0.0)

    def test_tag_total_uses_the_explicit_code(self):
        tag = self.Tag.create({"name": "Meal Benefit", "code": "MEALS"})
        self.rule_meal.tag_ids = tag
        rule = self.SalaryRule.create(
            {
                "name": "Meals Total",
                "code": "MEALS_TOTAL",
                "sequence": 23,
                "amount_select": "code",
                "amount_python_compute": "result = tags.MEALS",
            }
        )
        self.developer_pay_structure.rule_ids |= rule

        payslip = self._create_payslip()
        payslip.compute_sheet()

        # The meal rule is paid per worked day, so its total differs from the
        # unit amount shown on the line: tags sum totals.
        self.assertEqual(
            self._get_amount(payslip, "MEALS_TOTAL"),
            self._get_total(payslip, "MA"),
        )
        self.assertNotEqual(
            self._get_total(payslip, "MA"), self._get_amount(payslip, "MA")
        )

    def test_untagged_rules_are_not_counted(self):
        """HRA carries no tag, so it stays out of every tag total."""
        payslip = self._create_payslip()
        payslip.compute_sheet()

        hra = self._get_amount(payslip, "HRA")
        self.assertTrue(hra)
        self.assertEqual(
            self._get_amount(payslip, "TAXABLE_TOTAL"),
            self._get_amount(payslip, "BASIC") + self._get_amount(payslip, "SALE"),
        )

    def test_recomputing_does_not_double_the_totals(self):
        payslip = self._create_payslip()
        payslip.compute_sheet()
        first = self._get_amount(payslip, "TAXABLE_TOTAL")

        payslip.compute_sheet()

        self.assertEqual(self._get_amount(payslip, "TAXABLE_TOTAL"), first)

    def test_archived_tag_drops_out_of_the_totals(self):
        self.tag_taxable.active = False

        payslip = self._create_payslip()
        payslip.compute_sheet()

        self.assertEqual(self._get_amount(payslip, "TAXABLE_TOTAL"), 0.0)


class TestSalaryRuleTagSecurity(TestSalaryRuleTagCommon):
    """Access rights and the multi-company record rule."""

    def setUp(self):
        super().setUp()
        self.officer = self._create_user("officer", "payroll.group_payroll_user")
        self.manager = self._create_user("manager", "payroll.group_payroll_manager")

    def _create_user(self, login, group_xmlid):
        return self.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "email": f"{login}@example.org",
                "groups_id": [(6, 0, [self.env.ref(group_xmlid).id])],
            }
        )

    def test_officer_can_read_but_not_write(self):
        tag = self.tag_taxable.with_user(self.officer)
        self.assertEqual(tag.name, "Taxable")
        with self.assertRaises(AccessError):
            tag.sequence = 20

    def test_officer_cannot_create(self):
        with self.assertRaises(AccessError):
            self.Tag.with_user(self.officer).create({"name": "Bonus"})

    def test_manager_can_create_and_unlink(self):
        tag = self.Tag.with_user(self.manager).create({"name": "Bonus"})
        self.assertTrue(tag.exists())
        tag.unlink()
        self.assertFalse(tag.exists())

    def test_tags_of_other_companies_are_hidden(self):
        other_company = self.env["res.company"].create({"name": "Other Company"})
        other_tag = self.Tag.create(
            {"name": "Other Company Tag", "company_id": other_company.id}
        )
        visible = self.Tag.with_user(self.manager).search([])
        self.assertNotIn(other_tag, visible)
        self.assertIn(self.tag_taxable, visible)
