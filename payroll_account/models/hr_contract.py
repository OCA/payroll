# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = "hr.contract"
    _description = "Employee Contract"

    analytic_account_id = fields.Many2one(
        "account.analytic.account", "Analytic Account"
    )
    journal_id = fields.Many2one("account.journal", "Salary Journal")
