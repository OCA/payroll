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
        help=("Code for the tag. If not set the name will be used in uppercase.")
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
            "name_company_unique",
            "unique(name, company_id)",
            "Tag name must be unique per company!",
        ),
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

    @api.depends("salary_rules_ids")
    def _compute_salary_rules_count(self):
        """Compute the number of salary rules using each tag."""
        for tag in self:
            tag.salary_rules_count = len(tag.salary_rules_ids)

    @api.constrains("name")
    def _check_name_valid_identifier(self):
        """Ensure tag name can be used as a Python identifier when converted."""
        for tag in self:
            # Convert to uppercase and replace spaces/special chars with underscores
            identifier = self._normalize_code(tag.name)
            # Check if it's a valid Python identifier
            if not identifier.isidentifier():
                raise ValidationError(
                    _(
                        "Tag name '%(name)s' cannot be converted to a valid "
                        "Python identifier. Please use only letters, numbers, "
                        "and underscores, and don't start with a number.",
                        name=tag.name,
                    )
                )

    @api.constrains("code")
    def _check_code_valid_identifier(self):
        """Ensure tag code is a valid Python identifier if provided."""
        for tag in self:
            if tag.code and not tag.code.isidentifier():
                raise ValidationError(
                    _(
                        "Tag code '%(code)s' must be a valid Python identifier. "
                        "Please use only letters, numbers, and underscores, "
                        "and don't start with a number.",
                        code=tag.code,
                    )
                )

    @api.constrains("name", "code", "company_id")
    def _check_tag_code_unique(self):
        """Ensure no two tags of a company resolve to the same code.

        Salary rules address tag totals as ``tags.<CODE>``. Since the code
        falls back to the normalized name, tags with different names or with a
        code matching another tag's normalized name can end up sharing a code,
        silently adding up their amounts together.
        """
        for tag in self:
            tag_code = tag.get_tag_code()
            others = self.with_context(active_test=False).search(
                [
                    ("id", "!=", tag.id),
                    ("company_id", "=", tag.company_id.id),
                ]
            )
            duplicate = others.filtered(lambda t, c=tag_code: t.get_tag_code() == c)
            if duplicate:
                raise ValidationError(
                    _(
                        "Tag '%(name)s' resolves to the code '%(code)s', which is "
                        "already used by the tag '%(other)s'. Salary rules could "
                        "not tell the two totals apart, so please set a distinct "
                        "code or name.",
                        name=tag.name,
                        code=tag_code,
                        other=duplicate[0].name,
                    )
                )

    def get_tag_code(self):
        """Return the code to use in salary rule computations."""
        self.ensure_one()
        if self.code:
            return self.code
        # Read the source name, so that the code used by salary rules does not
        # change with the language the payslip is computed in.
        source_name = self.with_context(lang="en_US").name or self.name
        # Convert name to valid Python identifier
        return self._normalize_code(source_name)
