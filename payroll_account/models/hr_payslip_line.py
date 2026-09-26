# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    def _get_partner_id(self, credit_account):
        """
        Get partner_id of slip line to use in account_move_line

        Partner is required only for specific account types that track external
        relationships:
        - asset_receivable: Employee loans, salary advances, overpayments to recover
                           → Partner source: Employee (work_contact_id or
                             bank_account_id.partner_id)
        - liability_payable: Third-party payables (tax authorities, insurance
                            companies) typically managed through contribution
                            registers
                           → Partner source: Register partner
                             (salary_rule_id.register_id.partner_id)
        - liability_current: Current liabilities to pay employee salaries, net pay
                            accruals
                           → Partner source: Employee (work_contact_id or
                             bank_account_id.partner_id)

        For other account types (expense, income, asset_current, etc.), no partner
        is assigned as these represent internal accounting entries without external
        party relationships.
        """
        # Determine which account we're dealing with
        acc_type = (
            self.salary_rule_id.account_credit.account_type
            if credit_account
            else self.salary_rule_id.account_debit.account_type
        )

        if acc_type in ("asset_receivable", "liability_current"):
            # Employee-related accounts - always employee
            return (
                self.slip_id.employee_id.work_contact_id.id
                if self.slip_id.employee_id.work_contact_id
                else (
                    self.slip_id.employee_id.bank_account_id.partner_id.id
                    if self.slip_id.employee_id.bank_account_id
                    else False
                )
            )

        elif acc_type == "liability_payable":
            # Third-party payables - always register partner
            return (
                self.salary_rule_id.register_id.partner_id.id
                if self.salary_rule_id.register_id
                and self.salary_rule_id.register_id.partner_id
                else False
            )

        # All other account types (expense, income, etc.)
        return False
