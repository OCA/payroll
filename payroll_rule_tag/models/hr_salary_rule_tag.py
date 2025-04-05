# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class HrSalaryRuleTag(models.Model):
    _name = "hr.salary.rule.tag"
    _description = "Salary Rule Tag"
    _order = "name"

    name = fields.Char(required=True)
    salary_rules_ids = fields.Many2many("hr.salary.rule")
