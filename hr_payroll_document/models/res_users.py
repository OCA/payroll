# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.hr.models.res_users import HR_WRITABLE_FIELDS

HR_WRITABLE_FIELDS.append("no_payroll_encryption")


class ResUsers(models.Model):
    _inherit = "res.users"

    no_payroll_encryption = fields.Boolean(
        related="employee_id.no_payroll_encryption",
        readonly=False,
        related_sudo=False,
    )

    def action_get_attachment_tree_view(self):
        action = self.env.ref("base.action_attachment").sudo().read()[0]
        action["context"] = {
            "default_res_model": self._name,
            "default_res_id": self.employee_id.id,
        }
        action["domain"] = str(
            [
                ("document_type", "=", "payroll"),
                ("res_model", "=", self.employee_id._name),
                ("res_id", "in", [self.employee_id.id]),
            ]
        )
        return action
