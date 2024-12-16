# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def compute_sheet(self):
        # Set active_date in the context
        # To be used to filter active Master Data Values
        if not self.env.context.get("active_date"):
            self = self.with_context(active_date=self.date_to)
        return super().compute_sheet()
