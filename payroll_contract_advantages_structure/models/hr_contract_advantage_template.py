# Copyright 2026 INVITU (<https://www.invitu.com>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class HrContractAdvantageTemplate(models.Model):
    _inherit = "hr.contract.advantage.template"

    structure_ids = fields.Many2many(
        comodel_name="hr.payroll.structure",
        relation="hr_contract_advantage_template_structure_rel",
        column1="template_id",
        column2="structure_id",
        string="Salary Structures",
        help="Salary structures that auto-create this advantage on the"
        " contract when selected.",
    )
