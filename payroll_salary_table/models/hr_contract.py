# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class HrContract(models.Model):
    _inherit = "hr.contract"

    def get_data_record(self, code, date=None):
        self.ensure_one()
        contract = self.with_context(active_date=date) if date else self
        value_line = contract.active_values_ids.filtered(
            lambda x: x.type_id.code == code
            and (not date or not x.date_start or x.date_start <= date)
            and (not date or not x.date_end or x.date_end >= date)
        )
        return value_line[:1]

    def get_data_value(self, code, date=None):
        """
        Lookup on the Employee Master Data to find the value of a Data Type.
        Can be used in salary rules.
        code is a data type code.

        For example, to get the value for the BASIC code:
        value = contract.get_data_value("BASIC")

        The active_date should be set in the context, with the date to be used.

        """
        return self.get_data_record(code, date).get_value()
