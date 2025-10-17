# Copyright 2019 - Eficent http://www.eficent.com/
# Copyright 2019 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models
from odoo.exceptions import UserError


class HrPayslipChangeState(models.TransientModel):
    _name = "hr.payslip.change.state"
    _description = "Change state of a payslip"

    state = fields.Selection(
        selection=[
            ("draft", "Set to Draft"),
            ("verify", "Compute Sheet"),
            ("done", "Confirm"),
            ("cancel", "Cancel Payslip"),
        ],
        string="Action",
        help="* When the payslip is created the status is 'Draft'.\
             \n* If the payslip is under verification, the status is "
        "'Compute Sheet'. \
             \n* If the payslip is confirmed then status is set to 'Done'.\
             \n* When user cancel payslip the status is 'Rejected'.",
    )

    def change_state_confirm(self):
        record_ids = self.env.context.get("active_ids", False)
        payslip_obj = self.env["hr.payslip"]
        new_state = self.state
        records = payslip_obj.browse(record_ids)

        for rec in records:
            if new_state == "draft":
                if rec.state == "cancel":
                    rec.action_payslip_draft()
                else:
                    msg = self.env._(
                        "Only rejected payslips can be reset to draft, "
                        "the payslip %(nm)s is in %(st)s state",
                        nm=rec.name,
                        st=rec.state,
                    )
                    raise UserError(msg)
            elif new_state == "verify":
                if rec.state in ["draft", "verify"]:
                    rec.compute_sheet()
                else:
                    msg = self.env._(
                        "Only draft payslips can be verified, the "
                        "payslip %(nm)s is in %(st)s state",
                        nm=rec.name,
                        st=rec.state,
                    )
                    raise UserError(msg)
            elif new_state == "done":
                if rec.state in ("verify", "draft"):
                    rec.action_payslip_done()
                else:
                    msg = self.env._(
                        "Only payslips in states verify or draft can be "
                        "confirmed, the payslip %(nm)s is in %(st)s state",
                        nm=rec.name,
                        st=rec.state,
                    )
                    raise UserError(msg)
            elif new_state == "cancel":
                if rec.state != "cancel":
                    rec.action_payslip_cancel()
                else:
                    msg = self.env._(
                        "The payslip %(nm)s is already canceled please deselect it",
                        nm=rec.name,
                    )
                    raise UserError(msg)

        return {
            "domain": "[('id','in', [" + ",".join(map(str, record_ids)) + "])]",
            "name": self.env._("Payslips"),
            "view_mode": "list,form",
            "res_model": "hr.payslip",
            "view_id": False,
            "context": False,
            "type": "ir.actions.act_window",
        }
