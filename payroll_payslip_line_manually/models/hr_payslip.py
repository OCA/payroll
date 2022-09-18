from odoo import fields, models
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    line_manually_ids = fields.One2many(
        "hr.payslip.line.manually",
        "res_id",
        string="Manual Payslip Lines",
        domain=[("model", "=", "hr.payslip")],
        context={"default_model": "hr.payslip"},
        copy=True,
    )

    def _compute_payslip_line(
        self, rule, localdict, lines_dict, key, values_list, previous_amount
    ):
        # Should be values_list
        if not isinstance(values_list, list):
            values_list = [values_list]
        # For each dict in the values_list
        analytic_account_ids = []
        for values in values_list:
            # The dict should have a unique analytic account value (False is an option)
            # TODO: This is not working, I can add 2 lines with no analytic account!
            analytic_account_id = values.get("analytic_account_id")
            if analytic_account_id in analytic_account_ids:
                if analytic_account_id:
                    analytic_name = self.env["account.analytic.account"].browse(
                        analytic_account_id
                    ).name
                msg = "Please only one line with rule '{}' and analytic account '{}'!"
                return UserError(msg.format(rule.name, analytic_name))
            # Compute a payslip line
            key = (
                rule.code
                + "-"
                + str(localdict["contract"].id)
                + "-"
                + str(values.get("analytic_account_id"))
            )
            localdict, lines_dict = super(HrPayslip, self)._compute_payslip_line(
                rule, localdict, lines_dict, key, values, previous_amount
            )
        return localdict, lines_dict
