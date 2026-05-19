# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.version"
    _description = "Employee Contract"

    analytic_account_id = fields.Many2one(
        "account.analytic.account", "Analytic Account"
    )
    journal_id = fields.Many2one("account.journal", "Salary Journal")

    @api.model
    def _get_whitelist_fields_from_template(self):
        whitelist = super()._get_whitelist_fields_from_template()
        if "journal_id" not in whitelist:
            whitelist.append("journal_id")
        return whitelist
