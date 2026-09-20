# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    data_value_id = fields.Many2one(
        comodel_name="hr.data.type.value",
        readonly=True,
    )
