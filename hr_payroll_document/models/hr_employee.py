# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain


class Employee(models.Model):
    _inherit = "hr.employee"

    no_payroll_encryption = fields.Boolean(
        string="Disable payrolls encryption",
        help="If this is disabled (default), "
        "the PDF payrolls are encrypted using the Identification No.\n"
        "Only future payrolls are affected by this change, "
        "existing payrolls will not change their encryption status.",
        groups="hr.group_hr_user",
    )

    payroll_count = fields.Integer(
        compute="_compute_payroll_count",
    )

    def _validate_payroll_identification(self, code=None):
        # Override if the identification should be validated in another way
        if code is None and len(self) == 1:
            code = self.identification_id
        if country_code := self.env.company.country_id.code:
            is_valid = self.env["res.partner"]._check_vat_number(country_code, code)
        else:
            is_valid = True
        return is_valid

    @api.constrains("identification_id")
    def _constrain_payroll_identification(self):
        # Only check the employees that have an `identification_id`
        for employee in self.filtered("identification_id"):
            if not employee._validate_payroll_identification():
                raise ValidationError(
                    self.env._("The field identification ID is not valid")
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
        action = self.env["ir.actions.actions"]._for_xml_id("base.action_attachment")
        action["context"] = {
            "default_res_model": self._name,
            "default_res_id": self.ids[0],
        }
        action["domain"] = Domain(
            [
                ("document_type", "=", "payroll"),
                ("res_model", "=", self._name),
                ("res_id", "in", self.ids),
            ]
        )
        return action
