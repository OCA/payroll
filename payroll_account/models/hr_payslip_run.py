# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    journal_id = fields.Many2one(
        "account.journal",
        "Salary Journal",
        required=True,
        check_company=True,
        domain="[('company_id', '=', company_id)]",
        default=lambda self: self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", self.env.company.id)],
            limit=1,
        ),
    )
