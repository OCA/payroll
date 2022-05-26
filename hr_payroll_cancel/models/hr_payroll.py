# Copyright 2014 - Vauxoo http://www.vauxoo.com/
# Copyright 2017 ForgeFlow S.L.
#   (http://www.eficent.com)
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
#   (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    refunded_id = fields.Many2one(
        "hr.payslip", string="Refunded Payslip", readonly=True
    )

    def refund_sheet(self):
        res = super(HrPayslip, self).refund_sheet()
        self.write({"refunded_id": safe_eval(res["domain"])[0][2][0] or False})
        return res

    def action_payslip_cancel(self):
        for payslip in self:
            if payslip.refunded_id and payslip.refunded_id.state != "cancel":
                raise ValidationError(
                    _(
                        """To cancel the Original Payslip the
                    Refunded Payslip needs to be canceled first!"""
                    )
                )
            if not payslip.move_id.journal_id.restrict_mode_hash_table:
                payslip.move_id.with_context(force_delete=True).button_cancel()
                payslip.move_id.with_context(force_delete=True).unlink()
            else:
                payslip.move_id._reverse_moves()
                payslip.move_id = False
        return self.write({"state": "cancel"})
