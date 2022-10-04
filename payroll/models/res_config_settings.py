# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_payroll_account = fields.Boolean(string="Payroll Accounting")
    leaves_positive = fields.Boolean(
        config_parameter="payroll.leaves_positive",
        string="Leaves with positive values",
        help="Values for leaves (days and hours fields) "
        "should be positive instead of negative.",
    )
    allow_cancel_payslips = fields.Boolean(
        config_parameter="payroll.allow_cancel_payslips",
        string="Allow cancel confirmed payslips",
        help="If enabled, it allow the user to cancel confirmed payslips. Default: Not Enabled",
    )
    prevent_compute_on_confirm = fields.Boolean(
        config_parameter="payroll.prevent_compute_on_confirm",
        string="No compute on confirm",
        help="If enabled, this setting will prevent the payslip to be re-computed on confirm.",
        default=True,
    )
    allow_edit_payslip_lines = fields.Boolean(
        config_parameter="payroll.allow_edit_payslip_lines",
        string="Payslip lines editable",
        help="Allow editing payslip lines manually in views and forms",
        default=False,
    )
