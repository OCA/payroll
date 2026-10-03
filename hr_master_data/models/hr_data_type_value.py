# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class HrDataTypeValue(models.Model):
    _name = "hr.data.type.value"
    _description = "Master Data Value"
    _order = "sequence,name"

    name = fields.Char()
    code = fields.Char()
    sequence = fields.Integer()
    type_id = fields.Many2one(comodel_name="hr.data.type")
    active = fields.Boolean(default=True)
