# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    attendance_ids = fields.One2many(
        comodel_name="hr.attendance",
        compute="_compute_attendance_ids",
    )
    total_worked_hours = fields.Float(
        compute="_compute_attendance_ids",
    )

    @api.depends("date_from", "date_to", "employee_id")
    def _compute_attendance_ids(self):
        for slip in self:
            attendances = self.env["hr.attendance"].search(
                [
                    ("employee_id", "=", slip.employee_id.id),
                    ("check_in", ">=", slip.date_from),
                    ("check_in", "<=", slip.date_to),
                ],
                order="check_in ASC",
            )
            slip.attendance_ids = attendances
            slip.total_worked_hours = sum(att.worked_hours for att in attendances)
