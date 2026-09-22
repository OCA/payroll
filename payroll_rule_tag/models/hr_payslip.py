# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models

from odoo.addons.payroll.models.base_browsable import BrowsableObject


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _get_baselocaldict(self, contracts):
        localdict = super()._get_baselocaldict(contracts)
        localdict["tags"] = BrowsableObject(self.employee_id.id, {}, self.env)
        return localdict

    def _get_lines_dict(
        self, rule, localdict, lines_dict, key, values, previous_amount
    ):
        localdict, lines_dict = super()._get_lines_dict(
            rule, localdict, lines_dict, key, values, previous_amount
        )
        # sum the amount for salary rule tags
        total = lines_dict[key]["total"]
        for tag in rule.tag_ids:
            tag_code = tag.get_tag_code()
            localdict = self._sum_salary_rule_tag(
                localdict, tag_code, total - previous_amount
            )
        return localdict, lines_dict

    def _sum_salary_rule_tag(self, localdict, tag_code, amount):
        """Sum the amount for a specific salary rule tag.

        Args:
            localdict: The local dictionary containing all payslip variables
            tag_code: The code of the tag (already processed as valid Python identifier)
            amount: The amount to add to the tag total

        Returns:
            Updated localdict
        """
        self.ensure_one()
        if tag_code:
            localdict["tags"].dict[tag_code] = (
                localdict["tags"].dict.get(tag_code, 0) + amount
            )
        return localdict
