# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrContractAdvandageTemplate(models.Model):
    _name = "hr.contract.advantage.template"
    _description = "Employee's Advantage on Contract"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )

    lower_bound = fields.Monetary(
        currency_field="currency_id",
        help="Lower bound authorized by the employer for this advantage",
    )
    upper_bound = fields.Monetary(
        currency_field="currency_id",
        help="Upper bound authorized by the employer for this advantage",
    )
    default_value = fields.Monetary(currency_field="currency_id")
