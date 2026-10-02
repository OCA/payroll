# Copyright (C) 2021 Nimarosa (Nicolas Rodriguez) (<nicolasrsande@gmail.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        res = super().get_worked_day_lines(contracts, date_from, date_to)
        for contract in contracts.filtered(
            lambda contract: contract.resource_calendar_id
        ):
            # only use payslip day_from if it's greather than contract start date
            if date_from < contract.date_start:
                date_from = contract.date_start
            # == compute public holidays == #
            pholidays = self._compute_public_holidays_days(contract, date_from, date_to)
            if pholidays["number_of_days"] > 0:
                res.append(pholidays)
        return res

    def _compute_public_holidays_days(self, contract, date_from, date_to):
        # get public holidays list
        public_holidays = self.env["calendar.public.holiday"].get_holidays_list(
            year=date_from.year,
            start_dt=date_from,
            end_dt=date_to,
            partner_id=self._get_public_holidays_partner(contract).id,
        )
        ph_days = len(public_holidays)
        ph_hours = sum(
            self._get_public_holiday_hours(contract, holiday.date)
            for holiday in public_holidays
        )
        return {
            "name": _("Public Holidays Leaves"),
            "sequence": 10,
            "code": "PHOL",
            "number_of_days": ph_days,
            "number_of_hours": ph_hours,
            "contract_id": contract.id,
        }

    def _get_public_holidays_partner(self, contract):
        """The partner whose country and state decide the public holidays.

        Public holidays belong to the place where the employee works, so the
        employee's work address comes first. The employee's own contact or
        user partner is only a fallback: it usually carries the personal
        address, or no country at all, which made
        ``calendar.public.holiday.get_holidays_list()`` skip every holiday
        defined for a country.
        """
        employee = contract.employee_id
        return (
            employee.address_id
            or employee.user_id.partner_id
            or employee.work_contact_id
        )

    def _get_public_holiday_hours(self, contract, holiday_date):
        """Hours a public holiday is worth for ``contract``.

        The hours the contract's calendar schedules on that weekday (the
        contract's, not the employee's: it is the one the payslip is computed
        with). A holiday on a day the calendar does not schedule is worth an
        average working day of that calendar, computed from its attendances so
        it does not depend on ``hours_per_day`` having been filled. Without a
        calendar, 8 hours.
        """
        calendar = (
            contract.resource_calendar_id or contract.employee_id.resource_calendar_id
        )
        if not calendar:
            return 8.0
        attendances = calendar.attendance_ids.filtered(
            lambda att: not att.display_type
            and att.day_period != "lunch"
            and (not att.date_from or att.date_from <= holiday_date)
            and (not att.date_to or att.date_to >= holiday_date)
        )
        if calendar.two_weeks_calendar:
            week_type = str(
                self.env["resource.calendar.attendance"].get_week_type(holiday_date)
            )
            attendances = attendances.filtered(lambda att: att.week_type == week_type)
        same_day = attendances.filtered(
            lambda att: int(att.dayofweek) == holiday_date.weekday()
        )
        if same_day:
            return sum(att.hour_to - att.hour_from for att in same_day)
        working_days = set(attendances.mapped("dayofweek"))
        if not working_days:
            return calendar.hours_per_day or 8.0
        total = sum(att.hour_to - att.hour_from for att in attendances)
        return total / len(working_days)
