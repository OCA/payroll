# Copyright (C) 2021 Nimarosa (Nicolas Rodriguez) (<nicolasrsande@gmail.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, time

from odoo import _, api, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        res = super().get_worked_day_lines(contracts, date_from, date_to)
        for contract in contracts.filtered(
            lambda contract: contract.resource_calendar_id
        ):
            day_from = datetime.combine(date_from, time.min)
            day_to = datetime.combine(date_to, time.max)
            day_contract_start = datetime.combine(contract.date_start, time.min)
            # only use payslip day_from if it's greather than contract start date
            if day_from < day_contract_start:
                day_from = day_contract_start
            # == compute public holidays == #
            pholidays = self._compute_public_holidays_days(contract, day_from, day_to)
            if pholidays["number_of_days"] > 0:
                res.append(pholidays)
        return res

    def _compute_public_holidays_days(self, contract, day_from, day_to):
        # get public holidays list
        public_holidays = self.env["hr.holidays.public"].get_holidays_list(
            year=day_from.year,
            start_dt=day_from,
            end_dt=day_to,
            employee_id=contract.employee_id.id,
        )
        ph_days = len(public_holidays)
        ph_hours = ph_days * contract.employee_id.resource_calendar_id.hours_per_day
        return {
            "name": _("Public Holidays Leaves"),
            "sequence": 10,
            "code": "PHOL",
            "number_of_days": ph_days,
            "number_of_hours": ph_hours,
            "contract_id": contract.id,
        }
