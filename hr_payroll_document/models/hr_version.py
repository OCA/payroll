# Copyright 2026 Giuseppe Borruso - Dinamiche Aziendali Srl
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.exceptions import ValidationError


class HrVersionInherit(models.Model):
    _inherit = "hr.version"

    @api.constrains("identification_id")
    def _constrain_payroll_identification(self):
        for version in self.filtered("identification_id"):
            employee = version.employee_id or self.env["hr.employee"]
            if not employee._validate_payroll_identification(
                code=version.identification_id
            ):
                raise ValidationError(
                    self.env._("The field identification ID is not valid")
                )
