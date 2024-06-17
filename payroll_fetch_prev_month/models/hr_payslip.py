from dateutil.relativedelta import relativedelta

from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _date_hook(self, date_from, date_to):
        prev_month = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("payroll.worked_days_from_prev_month")
        )
        if prev_month:
            date_from -= relativedelta(months=1)
            date_to -= relativedelta(days=date_to.day)
        return date_from, date_to
