from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

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
