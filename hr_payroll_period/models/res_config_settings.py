from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    payroll_fiscalyear_creation_months_before = fields.Integer(
        related="company_id.payroll_fiscalyear_creation_months_before",
        readonly=False,
    )
