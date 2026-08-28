# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    @api.depends_context("active_date")
    @api.depends("contract_values_ids")
    def _compute_active_values_ids(self):
        "Returns the active values for the contract at a context given date"
        active_date = self.env.context.get("active_date")
        for contract in self:
            contract.active_values_ids = contract.contract_values_ids.filtered(
                lambda x: not active_date
                or (
                    (not x.date_start or x.date_start <= active_date)
                    and (not x.date_end or x.date_end >= active_date)
                )
            )

    contract_values_ids = fields.One2many(
        comodel_name="hr.employee.data.value",
        inverse_name="contract_id",
    )
    active_values_ids = fields.One2many(
        comodel_name="hr.employee.data.value",
        compute="_compute_active_values_ids",
    )

    def action_open_master_data(self):
        self.ensure_one()
        xmlid = "hr_master_data.action_hr_employee_data_value"
        action = self.env["ir.actions.actions"]._for_xml_id(xmlid)
        action.update(
            {
                "domain": [("contract_id", "=", self.id)],
                "context": {"default_contract_id": self.id},
            }
        )
        return action
