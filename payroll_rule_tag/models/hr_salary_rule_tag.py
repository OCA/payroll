# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrSalaryRuleTag(models.Model):
    _name = "hr.salary.rule.tag"
    _description = "Salary Rule Tag"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True,
        compute="_compute_code",
        store=True,
        readonly=False,
        precompute=True,
        help="Identifier salary rules use to read the tag total (tags.CODE). "
        "Proposed from the name when empty: uppercase, with anything that is "
        "not a letter, a number or an underscore replaced by an underscore.",
    )
    description = fields.Text(
        translate=True,
        help=(
            "Describe the purpose of this tag and how it should be used "
            "in salary calculations."
        ),
    )
    sequence = fields.Integer(default=10, help="Used to order tags in views")
    active = fields.Boolean(
        default=True,
        help="If unchecked, this tag will be hidden from most views "
        "without being deleted.",
    )
    color = fields.Integer(string="Color Index")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        help="Company to which this tag belongs",
    )
    salary_rules_ids = fields.Many2many(
        # No explicit relation table: the implicit one is the mirror of
        # hr.salary.rule.tag_ids, making both fields the two sides of the same
        # relation. It cannot be made explicit on the hr.salary.rule side,
        # because hr.payslip.line prototype-inherits that model and would end
        # up sharing the very same table and columns.
        "hr.salary.rule",
        string="Salary Rules",
        help="Salary rules that use this tag",
    )
    salary_rules_count = fields.Integer(
        compute="_compute_salary_rules_count",
        string="# Rules",
        store=True,
        help="Number of salary rules using this tag",
    )

    _sql_constraints = [
        (
            "code_company_unique",
            "unique(code, company_id)",
            "Tag code must be unique per company!",
        ),
    ]

    @api.model
    def _normalize_code(self, value):
        """Turn a free text value into an uppercase Python identifier."""
        return re.sub(r"[^a-zA-Z0-9_]", "_", (value or "").upper())

    @api.depends("name")
    def _compute_code(self):
        """Propose a code from the name, only while the tag has none.

        A tag that already has a code keeps it when renamed: salary rules
        address it as ``tags.<CODE>``, so changing it would break them. The
        source (English) name is used, so the proposal does not depend on the
        language of the user creating the tag.
        """
        for tag in self:
            if tag.code:
                tag.code = tag.code
                continue
            source_name = tag.with_context(lang="en_US").name or tag.name
            tag.code = self._normalize_code(source_name) or False

    @api.depends("salary_rules_ids")
    def _compute_salary_rules_count(self):
        """Compute the number of salary rules using each tag."""
        for tag in self:
            tag.salary_rules_count = len(tag.salary_rules_ids)

    @api.constrains("code")
    def _check_code_valid_identifier(self):
        """Ensure the tag has a code, and that it is a valid Python identifier."""
        for tag in self:
            if not tag.code:
                raise ValidationError(
                    _(
                        "Tag '%(name)s' needs a code: salary rules read its "
                        "total as tags.<CODE>.",
                        name=tag.name,
                    )
                )
            if not tag.code.isidentifier():
                raise ValidationError(
                    _(
                        "Tag code '%(code)s' must be a valid Python identifier. "
                        "Please use only letters, numbers, and underscores, "
                        "and don't start with a number.",
                        code=tag.code,
                    )
                )

    def get_tag_code(self):
        """Return the code to use in salary rule computations."""
        self.ensure_one()
        return self.code
