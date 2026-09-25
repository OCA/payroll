# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    analytic_account_id = fields.Many2one("account.analytic.account")
    account_tax_id = fields.Many2one("account.tax", "Tax")
    account_debit = fields.Many2one(
        "account.account",
        "Debit Account",
        domain=[("deprecated", "=", False)],
        company_dependent=True,
    )
    account_credit = fields.Many2one(
        "account.account",
        "Credit Account",
        domain=[("deprecated", "=", False)],
        company_dependent=True,
    )
    tax_base_id = fields.Many2one("hr.salary.rule", "Base")
    tax_line_ids = fields.One2many("hr.salary.rule", "tax_base_id", string="Tax lines")
