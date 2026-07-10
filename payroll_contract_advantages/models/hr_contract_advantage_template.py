# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrContractAdvandageTemplate(models.Model):
    _name = "hr.contract.advantage.template"
    _description = "Employee's Advantage on Contract"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    lower_bound = fields.Float(
        help="Lower bound authorized by the employer for this advantage"
    )
    upper_bound = fields.Float(
        help="Upper bound authorized by the employer for this advantage"
    )
    default_value = fields.Float()
