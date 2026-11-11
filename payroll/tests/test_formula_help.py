# Part of Odoo. See LICENSE file for full copyright and licensing details.

from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestFormulaHelp(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create({"name": "Richard"})
        cls.payslip = cls.env["hr.payslip"].create({"employee_id": cls.employee.id})

    def _formula_help(self):
        return self.env["hr.salary.rule"].new({"name": "Test Rule"}).formula_help

    def test_every_localdict_key_is_documented(self):
        """The help page must not drift away from what the formula gets."""
        localdict = self.payslip._get_baselocaldict(
            self.payslip._get_employee_contracts()
        )
        # "employee", "contract" and "payslip" are added to the local dict of
        # every rule in get_lines_dict(), on top of the base one.
        identifiers = list(localdict) + ["employee", "contract", "payslip"]
        formula_help = self._formula_help()
        for identifier in identifiers:
            self.assertIn(
                f"<code>{identifier}</code>",
                formula_help,
                f"'{identifier}' is available in a formula but is not documented",
            )

    def test_compute_variables_are_documented(self):
        formula_help = self._formula_help()
        for identifier in ["result", "result_qty", "result_rate", "result_name"]:
            self.assertIn(f"<code>{identifier}</code>", formula_help)

    def test_sections_are_escaped(self):
        sections = [("Title <b>", [("a & b", "<script>alert(1)</script>")])]
        rule = self.env["hr.salary.rule"]
        with patch.object(
            type(rule), "_get_formula_help_sections", lambda self: sections
        ):
            formula_help = self._formula_help()
        self.assertIn("Title &lt;b&gt;", formula_help)
        self.assertIn("a &amp; b", formula_help)
        self.assertIn("&lt;script&gt;", formula_help)
        self.assertNotIn("<script>", formula_help)

    def test_a_module_may_add_a_section(self):
        sections = [("My Module", [("my_object.my_value", "what it holds")])]
        rule = self.env["hr.salary.rule"]
        with patch.object(
            type(rule), "_get_formula_help_sections", lambda self: sections
        ):
            formula_help = self._formula_help()
        self.assertIn("<h3>My Module</h3>", formula_help)
        self.assertIn("<code>my_object.my_value</code>", formula_help)
        self.assertIn("what it holds", formula_help)
