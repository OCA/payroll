# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrContractAdvantage(models.Model):
    _name = "hr.contract.advantage"
    _description = "Employee's Advantages on Contract"

    _sql_constraints = [
        (
            "contract_template_unique",
            "unique(contract_id, advantage_template_id)",
            "This advantage is already set on this contract.",
        )
    ]

    contract_id = fields.Many2one("hr.contract", required=True, ondelete="cascade")
    advantage_template_id = fields.Many2one(
        "hr.contract.advantage.template", string="Advantage Template", required=True
    )
    advantage_template_code = fields.Char(
        string="Code", related="advantage_template_id.code", readonly=True
    )
    advantage_lower_bound = fields.Float(
        string="Lower Bound", related="advantage_template_id.lower_bound", readonly=True
    )
    advantage_upper_bound = fields.Float(
        string="Upper Bound", related="advantage_template_id.upper_bound", readonly=True
    )
    amount = fields.Float(digits="Payroll")

    @api.onchange("advantage_template_id")
    def _onchange_advantage_template_id(self):
        for record in self:
            record.amount = record.advantage_template_id.default_value

    @api.constrains("amount")
    def _check_bound_limits(self):
        for record in self:
            if not record.amount:
                continue
            # A bound left at 0.0 (the field default) means "no limit on that
            # side", so a template without explicit bounds doesn't block
            # every non-zero amount.
            if (
                record.advantage_upper_bound
                and record.amount > record.advantage_upper_bound
            ):
                raise ValidationError(
                    _("Advantage amount can't be greater than upper bound limit.")
                )
            if (
                record.advantage_lower_bound
                and record.amount < record.advantage_lower_bound
            ):
                raise ValidationError(
                    _("Advantage amount can't be less than lower bound limit.")
                )
