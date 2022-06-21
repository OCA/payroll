# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    advantages_ids = fields.One2many(
        "hr.contract.advantage", "contract_id", string="Contract Advantages"
    )
