# Copyright 2026 Anderson Oliveira
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class HrRuleParameter(models.Model):
    """A named payroll parameter whose value changes over time.

    Tax brackets, contribution rates and legal thresholds are data, not code.
    Keeping them here — versioned by the date they come into force — means a
    legal update is a new value with a new date, not an edit to every salary
    rule that happens to use it.
    """

    _name = "hr.rule.parameter"
    _description = "Salary Rule Parameter"
    _order = "code"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True,
        help="Unique identifier used from salary rules, "
        'e.g. payslip.rule_parameter("my_code").',
    )
    description = fields.Text(translate=True)
    country_id = fields.Many2one(
        "res.country",
        string="Country",
        help="Leave empty for parameters that are not country specific.",
    )
    parameter_value_ids = fields.One2many(
        "hr.rule.parameter.value",
        "rule_parameter_id",
        string="Values",
    )
    active = fields.Boolean(default=True)

    # Odoo 19 replaced the _sql_constraints list with models.Constraint
    # attributes; the old form is silently ignored.
    _code_uniq = models.Constraint(
        "unique (code)",
        "A salary rule parameter with this code already exists.",
    )

    @api.model
    def _get_parameter_from_code(self, code, date=None, raise_if_not_found=True):
        """Return the value of ``code`` in force on ``date``.

        :param str code: the parameter code
        :param date: date the value must be valid for; defaults to today
        :param bool raise_if_not_found: raise instead of returning False
        """
        if date is None:
            date = fields.Date.context_today(self)

        value = self.env["hr.rule.parameter.value"].search(
            [
                ("rule_parameter_id.code", "=", code),
                ("date_from", "<=", date),
            ],
            order="date_from desc",
            limit=1,
        )
        if value:
            return value._evaluated_value()

        if not raise_if_not_found:
            return False

        exists = self.search([("code", "=", code)], limit=1)
        if exists:
            raise UserError(
                self.env._(
                    "No value of the salary rule parameter '%(code)s' is in force "
                    "on %(date)s.",
                    code=code,
                    date=date,
                )
            )
        raise UserError(
            self.env._("No salary rule parameter with code '%(code)s'.", code=code)
        )


class HrRuleParameterValue(models.Model):
    """The value a parameter takes from a given date onwards."""

    _name = "hr.rule.parameter.value"
    _description = "Salary Rule Parameter Value"
    _order = "date_from desc"

    rule_parameter_id = fields.Many2one(
        "hr.rule.parameter",
        string="Parameter",
        required=True,
        ondelete="cascade",
    )
    code = fields.Char(related="rule_parameter_id.code", store=True)
    date_from = fields.Date(
        string="In force from",
        required=True,
        default=fields.Date.context_today,
    )
    parameter_value = fields.Text(
        required=True,
        help="Python literal. A number, or a structure such as a list of "
        "brackets: [(lower_limit, fixed_fee, rate), ...]",
    )

    _parameter_date_uniq = models.Constraint(
        "unique (rule_parameter_id, date_from)",
        "This parameter already has a value in force from that date.",
    )

    def _evaluated_value(self):
        """Return ``parameter_value`` as a Python object."""
        self.ensure_one()
        try:
            return safe_eval(self.parameter_value)
        except Exception as exc:
            raise UserError(
                self.env._(
                    "The value of salary rule parameter '%(code)s' in force from "
                    "%(date)s cannot be evaluated: %(error)s",
                    code=self.rule_parameter_id.code,
                    date=self.date_from,
                    error=exc,
                )
            ) from exc

    @api.depends("rule_parameter_id", "date_from")
    def _compute_display_name(self):
        for value in self:
            value.display_name = f"{value.rule_parameter_id.code} ({value.date_from})"
