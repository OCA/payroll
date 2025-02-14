# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrPayrollStructure(models.Model):
    """
    Salary structure used to defined
    - Basic
    - Allowances
    - Deductions
    """

    _name = "hr.payroll.structure"
    _description = "Salary Structure"

    @api.model
    def _get_parent(self):
        return self.env.ref("hr_payroll.structure_base", False)

    name = fields.Char(required=True)
    code = fields.Char(string="Reference")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        copy=False,
        default=lambda self: self.env.company,
    )
    note = fields.Text(string="Description")
    parent_id = fields.Many2one(
        "hr.payroll.structure", string="Parent", default=_get_parent
    )
    children_ids = fields.One2many(
        "hr.payroll.structure", "parent_id", string="Children", copy=True
    )
    rule_ids = fields.Many2many(
        "hr.salary.rule",
        "hr_structure_salary_rule_rel",
        "struct_id",
        "rule_id",
        string="Salary Rules",
    )
    require_code = fields.Boolean(
        "Require code",
        compute="_compute_require_code",
        default=lambda self: self._compute_require_code(),
    )

    def _compute_require_code(self):
        require = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("payroll.require_code_and_category")
        )
        self.require_code = require
        return require

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if self._has_cycle():
            raise ValidationError(_("You cannot create a recursive salary structure."))

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, code=_("%s (copy)") % self.code)
        return super().copy(default)

    def get_all_rules(self):
        """
        @return: recordset with all struct rules, ordered by sequence
        """
        return self.rule_ids._recursive_search_of_rules().sorted("sequence")

    def get_structure_with_parents(self):
        if not self:
            return self.env["hr.payroll.structure"]
        else:
            return self.parent_id.get_structure_with_parents() + self
