# Copyright 2026 INVITU (<https://www.invitu.com>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class HrContract(models.Model):
    _name = "hr.contract"
    _inherit = ["hr.contract.advantage.abstract", "hr.contract"]
