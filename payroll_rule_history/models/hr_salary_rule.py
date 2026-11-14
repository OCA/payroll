# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    has_history = fields.Boolean()
    # TODO: child rule name and code should sync with the parent rule
    base_rule_id = fields.Many2one(comodel_name="hr.salary.rule")
    history_rule_ids = fields.One2many(
        comodel_name="hr.salary.rule", inverse_name="base_rule_id"
    )

    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")
    # TODO: period overlap check

    def action_rule_history(self):
        self.ensure_one()
        return {
            # "name": _("Refund Payslip"),
            # "view_id": False,
            "res_model": "hr.salary.rule",
            "type": "ir.actions.act_window",
            "view_mode": "list, form",
            "target": "current",
            "domain": [("base_rule_id", "in", self.id)],
            "context": {"default_rule_id": self.id},
        }

    def _get_active_rule(self, date=None):
        rules = self.env["hr.salary.rule"]
        for rule in self:
            rules |= (
                rule.history_rule_ids.filtered(
                    lambda x: (not date and not x.date_start or x.date_start <= date)
                    and (not date or not x.date_end or date <= x.date_end)
                )
                if rule.has_history and rule.history_rule_ids
                else rule
            )
        return rules

    # Extension of payroll methods
    # ----------------------------

    def _compute_rule(self, localdict):
        # Method to evaluate the results of a salary rule
        # With history rules, replace the main rule
        # with the history rule active on the payslip date
        self = self._get_active_rule(localdict["payslip"].date_to)
        return super()._compute_rule(localdict)

    def _recursive_search_of_rules(self):
        # Method to return all rules following their parent-child relations
        # With history rules, replace therule
        # with the history rule active on the payslip date
        self = self._get_active_rule(self.env.context.get("active_date"))
        return super()._recursive_search_of_rules()
