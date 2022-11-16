# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrContractAdvantage(models.Model):
    _name = "hr.contract.advantage"
    _description = "Employee's Advantages on Contract"

    contract_id = fields.Many2one("hr.contract")
    advantage_template_id = fields.Many2one(
        "hr.contract.advantage.template", string="Advantage Template"
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
    amount = fields.Float()

    @api.onchange("advantage_template_id")
    def _onchange_advantage_template_id(self):
        for record in self:
            record.amount = record.advantage_template_id.default_value

    @api.constrains("amount")
    def _check_bound_limits(self):
        for record in self:
            if record.amount and record.amount != 0.00:
                if record.amount > record.advantage_upper_bound:
                    raise ValidationError(
                        _("Advantage amount can't be greater than upper bound limit.")
                    )
                elif record.amount < record.advantage_lower_bound:
                    raise ValidationError(
                        _("Advantage amount can't be less than lower bound limit.")
                    )
