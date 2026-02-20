# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    payroll_payslip_due_workdays = fields.Integer(
        string="Payslip due date workdays",
        default=5,
        help="Number of workdays after the payslip period end date to compute the due date.",
    )
