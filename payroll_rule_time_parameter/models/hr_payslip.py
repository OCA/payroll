# Copyright (C) 2021 Nimarosa (Nicolas Rodriguez) (<nicolasrsande@gmail.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def rule_parameter(self, code, return_type="float"):
        self.ensure_one()
        time_parameter = self.get_time_parameter(code, date=self.date_from)
        return (
            return_type == "float" and float(time_parameter) or time_parameter or 0.00
        )
