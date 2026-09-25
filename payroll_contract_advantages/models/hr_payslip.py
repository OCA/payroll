# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models

from odoo.addons.payroll.models.hr_payslip import BrowsableObject


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def get_current_contract_dict(self, contract, contracts):
        """Expose advantages by code in the salary rules localdict.

        The exposed value is the final amount (unit value x quantity),
        (re)evaluated per payslip so period-sensitive formulas stay
        correct. ``amount`` stays the unit value and is not overwritten.
        """
        self.ensure_one()
        res = super().get_current_contract_dict(contract, contracts)
        advantages_dict = {}
        for advantage in contract.advantages_ids:
            amount = advantage._compute_advantage_amount(payslip=self)
            advantages_dict[advantage.advantage_template_code] = amount
        res.update(
            {"advantages": BrowsableObject(self.employee_id, advantages_dict, self.env)}
        )
        return res
