# Copyright 2026 Anderson Oliveira
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _get_work_entries(self, contract, day_from, day_to):
        """Validated work entries of this contract overlapping the period."""
        return self.env["hr.work.entry"].search(
            [
                ("employee_id", "=", contract.employee_id.id),
                ("state", "=", "validated"),
                # Odoo 19 replaced date_start/date_stop with a single date.
                ("date", ">=", day_from),
                ("date", "<=", day_to),
            ]
        )

    def _work_entries_to_worked_days(self, work_entries, contract):
        """Group work entries by payroll code into worked-days lines.

        Hours come straight from the entries. Days are derived from the
        contract's calendar rather than assumed to be 8: a part-time or a
        12-hour shift must not be counted as if it were a standard day.
        """
        hours_per_day = contract.resource_calendar_id.hours_per_day or 8.0

        grouped = {}
        for entry in work_entries:
            work_type = entry.work_entry_type_id
            if not work_type.code:
                # A type with no payroll code cannot be addressed from a rule.
                continue
            line = grouped.setdefault(
                work_type.code,
                {
                    "name": work_type.name,
                    "code": work_type.code,
                    "sequence": work_type.sequence,
                    "contract_id": contract.id,
                    "number_of_days": 0.0,
                    "number_of_hours": 0.0,
                },
            )
            line["number_of_hours"] += entry.duration

        for line in grouped.values():
            line["number_of_days"] = line["number_of_hours"] / hours_per_day

        return sorted(grouped.values(), key=lambda line: line["sequence"])

    def get_worked_day_lines(self, contracts, date_from, date_to):
        """Prefer real work entries over the theoretical calendar.

        ``payroll`` derives worked days from the resource calendar, i.e. what
        *should* have been worked. Where work entries exist they describe what
        actually was — attendances, overtime, absences — so they win.

        Contracts with no work entry in the period keep the calendar behaviour,
        so installing this module changes nothing for those.
        """
        self.ensure_one()
        res = []
        remaining = self.env["hr.version"]

        for contract in contracts:
            work_entries = self._get_work_entries(contract, date_from, date_to)
            if work_entries:
                res.extend(self._work_entries_to_worked_days(work_entries, contract))
            else:
                remaining |= contract

        if remaining:
            res.extend(super().get_worked_day_lines(remaining, date_from, date_to))
        return res
