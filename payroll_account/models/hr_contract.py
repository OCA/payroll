# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class HrContract(models.Model):
    _inherit = "hr.version"
    _description = "Employee Contract / Version"

    analytic_account_id = fields.Many2one(
        "account.analytic.account", "Analytic Account"
    )
    journal_id = fields.Many2one("account.journal", "Salary Journal")
