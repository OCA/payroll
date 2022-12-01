# Copyright (C) 2021 Nimarosa (Nicolas Rodriguez) (<nicolasrsande@gmail.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def rule_parameter(self, code, date=False, get="value"):
        self.ensure_one()
        if not date:
            date = self.date_from
        time_parameter = self.get_time_parameter(code, date=date, get=get)
        return time_parameter
