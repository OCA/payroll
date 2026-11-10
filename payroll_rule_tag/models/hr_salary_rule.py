# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    tag_ids = fields.Many2many(
        "hr.salary.rule.tag",
        string="Tags",
        domain="[('company_id', 'in', [company_id, False])]",
        help="Tags to categorize this salary rule for reporting and calculations",
    )
