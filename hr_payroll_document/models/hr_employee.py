from odoo import _, fields, models
from odoo.exceptions import ValidationError


class Employee(models.Model):
    _inherit = "hr.employee"

    no_payroll_encryption = fields.Boolean(
        string="Disable payrolls encryption",
        help="If this is disabled (default), "
        "the PDF payrolls are encrypted using the Identification No.\n"
        "Only future payrolls are affected by this change, "
        "existing payrolls will not change their encryption status.",
    )

    payroll_count = fields.Integer(
        compute="_compute_payroll_count",
    )

    def _compute_payroll_count(self):
        self.payroll_count = len(
            self.env["ir.attachment"].search(
                [
                    ("document_type", "=", "payroll"),
                    ("res_model", "=", self._name),
                    ("res_id", "in", self.ids),
                ]
            )
        )

    def action_get_payroll_tree_view(self):
        action = self.env.ref("base.action_attachment").sudo().read()[0]
        action["context"] = {
            "default_res_model": self._name,
            "default_res_id": self.ids[0],
        }
        action["domain"] = str(
            [
                ("document_type", "=", "payroll"),
                ("res_model", "=", self._name),
                ("res_id", "in", self.ids),
            ]
        )
        return action

    def write(self, vals):
        res = super().write(vals)
        if "identification_id" in vals and not self.env["res.partner"].simple_vat_check(
            self.env.company.country_id.code, vals["identification_id"]
        ):
            raise ValidationError(_("The field identification ID is not valid"))
        return res
