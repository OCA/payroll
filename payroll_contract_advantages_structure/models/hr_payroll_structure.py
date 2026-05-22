# Copyright 2026 INVITU (<https://www.invitu.com>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class HrPayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"

    advantage_template_ids = fields.Many2many(
        comodel_name="hr.contract.advantage.template",
        relation="hr_contract_advantage_template_structure_rel",
        column1="structure_id",
        column2="template_id",
        string="Advantage Templates",
        help="Templates auto-created on a contract when this structure" " is selected.",
    )
