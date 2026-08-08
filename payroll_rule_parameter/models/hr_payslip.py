# Copyright 2026 Anderson Oliveira
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def rule_parameter(self, code):
        """Value of the parameter ``code`` in force during this payslip.

        Meant to be called from a salary rule::

            brackets = payslip.rule_parameter("income_tax_brackets")

        The date used is the payslip's ``date_to``, not today: recomputing an
        old payslip must yield the rates that applied back then, not the
        current ones.
        """
        self.ensure_one()
        return self.env["hr.rule.parameter"]._get_parameter_from_code(
            code, self.date_to
        )
