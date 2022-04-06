import ast

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrSalaryRuleParameterValue(models.Model):
    _name = "hr.rule.parameter.value"
    _description = "Salary Rule Parameter Value"
    _order = "date_from desc"

    rule_parameter_id = fields.Many2one(
        "hr.rule.parameter", required=True, ondelete="cascade"
    )
    code = fields.Char(related="rule_parameter_id.code", store=True, readonly=True)
    date_from = fields.Date(string="Date From", required=True)
    parameter_value = fields.Text(help="Python Code")
    country_id = fields.Many2one(related="rule_parameter_id.country_id")
    company_id = fields.Many2one(related="rule_parameter_id.company_id")

    _sql_constraints = [
        (
            "_unique",
            "unique (rule_parameter_id, date_from)",
            "Two rules parameters with the same code cannot start the same day",
        ),
    ]


class HrSalaryRuleParameter(models.Model):
    _name = "hr.rule.parameter"
    _description = "Salary Rule Parameter"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    description = fields.Text("Description")
    country_id = fields.Many2one(
        "res.country",
        string="Country",
        default=lambda self: self.env.company.country_id,
    )
    parameter_version_ids = fields.One2many(
        "hr.rule.parameter.value", "rule_parameter_id", string="Versions"
    )
    company_id = fields.Many2one(
        "res.company", "Company", required=True, default=lambda self: self.env.company
    )

    @api.model
    def _get_parameter_from_code(self, code, date=None):
        if not date:
            date = fields.Date.today()
        rule_parameter = self.env["hr.rule.parameter.value"].search(
            [
                ("code", "=", code),
                ("date_from", "<=", date),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        if rule_parameter:
            return ast.literal_eval(rule_parameter.parameter_value)
        else:
            raise UserError(
                _("No rule parameter with code '%s' was found for %s ") % (code, date)
            )

    _sql_constraints = [
        (
            "_unique",
            "unique (code, company_id)",
            "Two rule parameters cannot have the same code.",
        ),
    ]
