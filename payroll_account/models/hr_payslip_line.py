# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    def _get_partner_id(self, credit_account):
        """
        Get partner_id of slip line to use in account_move_line
        """
        # use partner of salary rule or fallback on employee's address
        register_partner_id = self.salary_rule_id.register_id.partner_id
        acc_type = self.salary_rule_id.account_debit.account_type
        if credit_account:
            acc_type = self.salary_rule_id.account_credit.account_type
        if register_partner_id or acc_type in ("asset_receivable", "liability_payable"):
            return register_partner_id.id
        return False
