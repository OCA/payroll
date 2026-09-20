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
            localdict = self._sum_salary_rule_tag(
                localdict, tag.name, total - previous_amount
            )
        return localdict, lines_dict

    def _sum_salary_rule_tag(self, localdict, tag_name, amount):
        self.ensure_one()
        if tag_name:
            code = tag_name.upper()
            localdict["tags"].dict[code] = localdict["tags"].dict.get(code, 0) + amount
        return localdict
