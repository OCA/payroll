# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class HrDataValueReason(models.Model):
    _name = "hr.data.value.reason"
    _description = "Master Data Change Reason"
    _order = "code,name"

    name = fields.Char()
    code = fields.Char()
    active = fields.Boolean(default=True)
