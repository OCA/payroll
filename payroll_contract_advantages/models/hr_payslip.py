# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models

from odoo.addons.payroll.models.hr_payslip import BrowsableObject


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def get_current_contract_dict(self, contract, contracts):
        self.ensure_one()
        res = super().get_current_contract_dict(contract, contracts)
        advantages_dict = {}
        for advantage in contract.advantages_ids:
            advantages_dict[advantage.advantage_template_code] = advantage.amount
        res.update(
            {"advantages": BrowsableObject(self.employee_id, advantages_dict, self.env)}
        )
        return res
