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
        partner_id = (
            register_partner_id.id or self.slip_id.employee_id.address_home_id.id
        )
        if credit_account:
            if (
                register_partner_id
                or self.salary_rule_id.account_credit.internal_type
                in ("receivable", "payable")
            ):
                return partner_id
        else:
            if (
                register_partner_id
                or self.salary_rule_id.account_debit.internal_type
                in ("receivable", "payable")
            ):
                return partner_id
        return False
