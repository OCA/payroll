# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

PAYABLE_RECEIVABLE_TYPES = ("asset_receivable", "liability_payable")


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    payment_status = fields.Selection(
        selection=[("paid", "Paid"), ("not_paid", "Not Paid")],
        compute="_compute_payment_status",
    )

    @api.depends("move_id.line_ids.full_reconcile_id")
    def _compute_payment_status(self):
        for slip in self:
            if not slip.move_id:
                slip.payment_status = False
                continue
            payable_receivable_lines = slip.move_id.line_ids.filtered(
                lambda line: line.account_id.account_type in PAYABLE_RECEIVABLE_TYPES
            )
            if not payable_receivable_lines:
                slip.payment_status = False
            elif all(line.full_reconcile_id for line in payable_receivable_lines):
                slip.payment_status = "paid"
            else:
                slip.payment_status = "not_paid"

    def action_payslip_done(self):
        res = super().action_payslip_done()
        for slip in self:
            if not slip.move_id or not slip.date_payment:
                continue
            lines_to_update = slip.move_id.line_ids.filtered(
                lambda line: line.account_id.account_type in PAYABLE_RECEIVABLE_TYPES
            )
            if lines_to_update:
                lines_to_update.write({"date_maturity": slip.date_payment})
        return res
