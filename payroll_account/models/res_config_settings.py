# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    action_group_payslips = fields.Boolean(
        string="Group payslips in accounting",
        related="company_id.action_group_payslips",
        help="Allow companies to group payslips in accounting",
        readonly=False,
        store=True,
    )
