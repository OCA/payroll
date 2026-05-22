# Copyright 2026 INVITU (<https://www.invitu.com>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    def _get_applicable_advantage_templates(self):
        """Templates rattached to the contract's salary structure."""
        self.ensure_one()
        return self.struct_id.advantage_template_ids

    @api.onchange("struct_id")
    def _onchange_struct_id_sync_advantages(self):
        for contract in self:
            contract._sync_advantages_from_templates()
