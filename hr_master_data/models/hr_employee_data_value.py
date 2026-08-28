# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class HrEmployeeDataValue(models.Model):
    _name = "hr.employee.data.value"
    _description = "Employee Master Data Value"
    _order = "date_start desc"

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        related="contract_id.employee_id",
        store=True,
        readonly=False,
    )
    contract_id = fields.Many2one(comodel_name="hr.contract")
    company_id = fields.Many2one(
        comodel_name="res.company", related="contract_id.company_id", store=True
    )
    date_start = fields.Date(required=True)
    date_end = fields.Date()
    type_id = fields.Many2one(comodel_name="hr.data.type", required=True)
    group_id = fields.Many2one(related="type_id.group_id", store=True)
    value_type = fields.Selection(related="type_id.value_type")
    value_bool = fields.Boolean(string="Yes/No")
    value_float = fields.Float(string="Number")
    value_id = fields.Many2one(
        comodel_name="hr.data.type.value",
        domain="[('type_id', '=', type_id)]",
    )
    reason_id = fields.Many2one(comodel_name="hr.data.value.reason")
    note = fields.Text()

    def get_value(self):
        self.ensure_one()
        if self.value_type == "bool":
            return self.value_bool
        elif self.value_type == "float":
            return self.value_float
        elif self.value_type == "id":
            return self.value_id.id
