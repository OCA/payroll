# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, models


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    def _get_formula_help_sections(self):
        """Document what this module adds to "current_contract"."""
        sections = super()._get_formula_help_sections()
        sections.append(
            (
                _("Contract advantages"),
                [
                    (
                        "current_contract.advantages.CODE",
                        _(
                            "the amount of the advantage of the current contract "
                            "whose template code is CODE"
                        ),
                    ),
                ],
            )
        )
        return sections
