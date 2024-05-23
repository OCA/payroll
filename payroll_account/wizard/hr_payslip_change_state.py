# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class HrPayslipChangeState(models.TransientModel):

    _inherit = "hr.payslip.change.state"

    def change_state_confirm(self):
        company_id = self.env.company.id
        config_settings = self.env["res.config.settings"].search(
            [("company_id", "=", company_id)], limit=1
        )
        action_group_payslips = config_settings.action_group_payslips

        if action_group_payslips and self.state == "done":
            record_ids = self.env.context.get("active_ids", False)
            payslip_obj = self.env["hr.payslip"]
            records = payslip_obj.browse(record_ids)
            for rec in records:
                if rec.state not in ("verify", "draft"):
                    raise UserError(
                        _(
                            "Only payslips in states verify or draft"
                            " can be confirmed, the payslip %(nm)s is in "
                            "%(st)s state"
                        )
                        % {"nm": rec.name, "st": rec.state}
                    )
            records.action_payslip_done()
        else:
            return super(HrPayslipChangeState, self).change_state_confirm()
