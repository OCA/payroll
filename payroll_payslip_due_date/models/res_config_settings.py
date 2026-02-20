# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    payroll_payslip_due_workdays = fields.Integer(
        related="company_id.payroll_payslip_due_workdays",
        readonly=False,
        string="Payslip due date workdays",
    )
