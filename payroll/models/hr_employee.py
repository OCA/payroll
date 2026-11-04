# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    payroll_slip_ids = fields.One2many(
        "payroll.payslip", "employee_id", string="Payslips", readonly=True
    )
    payroll_slip_count = fields.Integer(
        compute="_compute_payroll_slip_count",
        groups="payroll.group_payroll_user",
    )

    def _compute_payroll_slip_count(self):
        for employee in self:
            employee.payroll_slip_count = len(employee.payroll_slip_ids)
