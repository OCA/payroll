# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class HrPayslipEmployees(models.TransientModel):
    _inherit = "hr.payslip.employees"

    def compute_sheet(self):
        if self.env.context.get("active_id"):
            journal_id = (
                self.env["hr.payslip.run"]
                .browse(self.env.context.get("active_id"))
                .journal_id.id
            )
            self = self.with_context(default_journal_id=journal_id)
        return super().compute_sheet()
