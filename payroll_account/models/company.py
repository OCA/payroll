# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    action_group_payslips = fields.Boolean(
        string="Group payslips in accounting",
        help="Allow companies to group payslips in accounting",
    )
