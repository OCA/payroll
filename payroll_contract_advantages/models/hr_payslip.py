# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models

from odoo.addons.payroll.models.hr_payslip import BrowsableObject


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def get_current_contract_dict(self, contract, contracts):
        """Expose advantages by code in the salary rules localdict.

        Amounts are (re)evaluated per payslip from each advantage's
        formula, so period-sensitive values stay correct. In 'fixed'
        mode the value equals the stored amount, unchanged for existing
        installations.
        """
        self.ensure_one()
        res = super().get_current_contract_dict(contract, contracts)
        advantages_dict = {}
        for advantage in contract.advantages_ids:
            amount = advantage._compute_advantage_amount(payslip=self)
            # Keep the stored amount in sync for reporting / auditing.
            if advantage.amount != amount:
                advantage.amount = amount
            advantages_dict[advantage.advantage_template_code] = amount
        res.update(
            {"advantages": BrowsableObject(self.employee_id, advantages_dict, self.env)}
        )
        return res
