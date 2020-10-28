# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrSalaryRuleCategory(models.Model):
    _name = "hr.salary.rule.category"
    _description = "Salary Rule Category"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    parent_id = fields.Many2one(
        "hr.salary.rule.category",
        string="Parent",
        help="Linking a salary category to its parent is used only for the "
        "reporting purpose.",
    )
    children_ids = fields.One2many(
        "hr.salary.rule.category", "parent_id", string="Children"
    )
    note = fields.Text(string="Description")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(
                _(
                    "Error! You cannot create recursive hierarchy of Salary "
                    "Rule Category."
                )
            )
