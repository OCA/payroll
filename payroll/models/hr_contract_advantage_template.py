# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrContractAdvandageTemplate(models.Model):
    _name = "hr.contract.advantage.template"
    _description = "Employee's Advantage on Contract"

    name = fields.Char("Name", required=True)
    code = fields.Char("Code", required=True)
    lower_bound = fields.Float(
        "Lower Bound", help="Lower bound authorized by the employer for this advantage"
    )
    upper_bound = fields.Float(
        "Upper Bound", help="Upper bound authorized by the employer for this advantage"
    )
    default_value = fields.Float("Default value for this advantage")
