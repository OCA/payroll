# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class HrDataType(models.Model):
    _name = "hr.data.type"
    _description = "Master Data Type"
    _order = "code,name"

    name = fields.Char(required=True)
    code = fields.Char()
    value_type = fields.Selection(
        selection=[("bool", "Yes/No"), ("float", "Numeric"), ("id", "Selection Value")],
        required=True,
    )
    group_id = fields.Many2one(comodel_name="hr.data.group")
    active = fields.Boolean(default=True)
    values_ids = fields.One2many(
        comodel_name="hr.data.type.value", inverse_name="type_id"
    )
