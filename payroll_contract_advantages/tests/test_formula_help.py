# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import TransactionCase


class TestFormulaHelp(TransactionCase):
    def test_advantages_are_documented(self):
        """What this module adds to the formulas shows in the Help page."""
        rule = self.env["hr.salary.rule"].new({"name": "Test Rule"})
        self.assertIn("<h3>Contract advantages</h3>", rule.formula_help)
        self.assertIn(
            "<code>current_contract.advantages.CODE</code>", rule.formula_help
        )
