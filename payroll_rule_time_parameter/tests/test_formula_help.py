from odoo.tests.common import TransactionCase


class TestFormulaHelp(TransactionCase):
    def test_rule_parameter_is_documented(self):
        """The helper of this module shows in the Help page of a salary rule."""
        rule = self.env["hr.salary.rule"].new({"name": "Test Rule"})
        self.assertIn("<h3>Rule parameters</h3>", rule.formula_help)
        self.assertIn("payslip.rule_parameter(", rule.formula_help)
