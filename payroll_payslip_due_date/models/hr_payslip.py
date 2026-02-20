# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime, time, timedelta

from pytz import UTC

from odoo import api, fields, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    payment_due_date = fields.Date(
        compute="_compute_payment_due_date",
        store=True,
        readonly=True,
    )
    payment_due_is_overdue = fields.Boolean(
        compute="_compute_payment_due_flags",
        store=False,
        readonly=True,
    )
    payment_due_is_ok = fields.Boolean(
        compute="_compute_payment_due_flags",
        store=False,
        readonly=True,
    )

    @api.depends(
        "date_to",
        "contract_id.resource_calendar_id",
        "employee_id.resource_calendar_id",
        "company_id.resource_calendar_id",
        "company_id.payroll_payslip_due_workdays",
    )
    def _compute_payment_due_date(self):
        for slip in self:
            slip.payment_due_date = False
            if not slip.date_to:
                continue

            workdays = slip.company_id.payroll_payslip_due_workdays or 0
            if workdays <= 0:
                slip.payment_due_date = slip.date_to
                continue

            calendar = (
                slip.contract_id.resource_calendar_id
                or slip.employee_id.resource_calendar_id
                or slip.company_id.resource_calendar_id
            )
            start_date = slip.date_to + timedelta(days=1)
            start_dt = datetime.combine(start_date, time.min).replace(tzinfo=UTC)
            planned_dt = calendar.plan_days(workdays, start_dt, compute_leaves=True)
            slip.payment_due_date = planned_dt.date() if planned_dt else False

    @api.depends("payment_due_date")
    def _compute_payment_due_flags(self):
        today = fields.Date.today()
        for slip in self:
            slip.payment_due_is_overdue = (
                bool(slip.payment_due_date) and slip.payment_due_date < today
            )
            slip.payment_due_is_ok = (
                bool(slip.payment_due_date) and slip.payment_due_date >= today
            )
