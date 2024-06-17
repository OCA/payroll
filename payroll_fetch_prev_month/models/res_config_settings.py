# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    worked_days_from_prev_month = fields.Boolean(
        config_parameter="payroll.worked_days_from_prev_month",
        string="Fetch worked days and leaves from the previous month",
        help="instead of the current month",
        default=False,
    )
