from odoo import fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    line_manually_ids = fields.One2many(
        "hr.payslip.line.manually",
        "res_id",
        string="Recurring Payslip Lines",
        domain=[("model", "=", "hr.contract")],
        context={"default_model": "hr.contract"},
        copy=True,
    )
