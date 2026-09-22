# Copyright (C) 2021 Nimarosa (Nicolas Rodriguez) (<nicolasrsande@gmail.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    def _get_formula_help_sections(self):
        """Document the helper this module adds to the payslip."""
        sections = super()._get_formula_help_sections()
        sections.append(
            (
                _("Rule parameters"),
                [
                    (
                        'payslip.rule_parameter("CODE")',
                        _(
                            "the value of the rule parameter with that code, at "
                            "the start date of the payslip"
                        ),
                    ),
                    (
                        'payslip.rule_parameter("CODE", date=payslip.date_to)',
                        _("the value at another date"),
                    ),
                    (
                        'payslip.rule_parameter("CODE", get="date")',
                        _("the start date of the version the value comes from"),
                    ),
                ],
            )
        )
        return sections
