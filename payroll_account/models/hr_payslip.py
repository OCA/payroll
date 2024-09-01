# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    date = fields.Date(
        "Date Account",
        states={"draft": [("readonly", False)]},
        readonly=True,
        help="Keep empty to use the period of the validation(Payslip) date.",
    )
    journal_id = fields.Many2one(
        "account.journal",
        "Salary Journal",
        readonly=True,
        required=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env["account.journal"].search(
            [("type", "=", "general")], limit=1
        ),
    )
    move_id = fields.Many2one(
        "account.move", "Accounting Entry", readonly=True, copy=False
    )

    @api.model
    def create(self, vals):
        if "journal_id" in self.env.context:
            vals["journal_id"] = self.env.context.get("journal_id")
        return super(HrPayslip, self).create(vals)

    @api.onchange("contract_id")
    def onchange_contract(self):
        super(HrPayslip, self).onchange_contract()
        self.journal_id = (
            self.contract_id.journal_id.id
            or (not self.contract_id and self.default_get(["journal_id"])["journal_id"])
            or self.journal_id
        )

    def action_payslip_cancel(self):
        for payslip in self:
            if not payslip.move_id.journal_id.restrict_mode_hash_table:
                payslip.move_id.with_context(force_delete=True).button_cancel()
                payslip.move_id.with_context(force_delete=True).unlink()
            else:
                payslip.move_id._reverse_moves()
                payslip.move_id = False
        return super(HrPayslip, self).action_payslip_cancel()

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()

        payslips_by_run = {}
        individual_payslips = self.env["hr.payslip"]

        for slip in self:
            if slip.payslip_run_id:
                if slip.payslip_run_id not in payslips_by_run:
                    payslips_by_run[slip.payslip_run_id] = self.env["hr.payslip"]
                payslips_by_run[slip.payslip_run_id] |= slip
            else:
                individual_payslips |= slip

        # Process payslips with payslip_run_id
        for payslip_run, _slips in payslips_by_run.items():
            all_run_slips = self.env["hr.payslip"].search(
                [("payslip_run_id", "=", payslip_run.id)]
            )
            done_run_slips = all_run_slips.filtered(lambda s: s.state == "done")

            if set(done_run_slips) == set(all_run_slips):
                # This is the last batch of payslips being confirmed for this run
                self._create_grouped_move_for_payslips(all_run_slips)

        # Process individual payslips (without payslip_run_id)
        for slip in individual_payslips:
            self._create_move_for_payslip(slip)

        return res

    def _create_grouped_move_for_payslips(self, slips):
        if not slips:
            return

        grouped_lines = {}
        date = max(slip.date or slip.date_to for slip in slips)
        currency = (
            slips[0].company_id.currency_id
            or slips[0].journal_id.company_id.currency_id
        )

        for slip in slips:
            for line in slip.line_ids:
                amount = currency.round(slip.credit_note and -line.total or line.total)
                if currency.is_zero(amount):
                    continue

                for account_id in [
                    line.salary_rule_id.account_debit.id,
                    line.salary_rule_id.account_credit.id,
                ]:
                    if not account_id:
                        continue

                    key = (
                        account_id,
                        line._get_partner_id(
                            account_id == line.salary_rule_id.account_credit.id
                        ),
                        line.salary_rule_id.analytic_account_id.id
                        or slip.contract_id.analytic_account_id.id,
                        line.salary_rule_id.account_tax_id.id,
                    )

                    if key not in grouped_lines:
                        grouped_lines[key] = {
                            "name": line.name,
                            "debit": 0.0,
                            "credit": 0.0,
                            "account_id": account_id,
                            "partner_id": key[1],
                            "analytic_account_id": key[2],
                            "tax_line_id": key[3],
                            "tax_ids": [
                                (4, tax.id, 0)
                                for tax in line.salary_rule_id.tax_line_ids
                            ],
                            "tax_tag_ids": self._get_tax_tag_ids(line),
                            "tax_repartition_line_id": self._get_tax_repartition_line_id(
                                line, account_id
                            ),
                        }

                    if account_id == line.salary_rule_id.account_debit.id:
                        grouped_lines[key]["debit"] += amount > 0.0 and amount or 0.0
                        grouped_lines[key]["credit"] += amount < 0.0 and -amount or 0.0
                    else:
                        grouped_lines[key]["debit"] += amount < 0.0 and -amount or 0.0
                        grouped_lines[key]["credit"] += amount > 0.0 and amount or 0.0

        # Prepare move dict
        move_dict = {
            "narration": _("Payslips for run %s") % slips[0].payslip_run_id.name,
            "ref": slips[0].payslip_run_id.name,
            "journal_id": slips[0].journal_id.id,
            "date": date,
            "line_ids": [(0, 0, line_value) for line_value in grouped_lines.values()],
        }

        # Create and post move
        move = self.env["account.move"].create(move_dict)
        move.action_post()

        # Update all payslips with the created move
        for slip in slips:
            slip.write({"move_id": move.id, "date": date})

    def _get_tax_tag_ids(self, line):
        tax_tag_ids = self.env["account.account.tag"]
        if line.salary_rule_id.tax_line_ids:
            tax_tag_ids |= (
                self.env["account.tax.repartition.line"]
                .search(
                    [
                        (
                            "invoice_tax_id",
                            "in",
                            line.salary_rule_id.tax_line_ids.mapped("id"),
                        ),
                        ("repartition_type", "=", "base"),
                    ]
                )
                .mapped("tag_ids")
            )

        if line.salary_rule_id.account_tax_id:
            repartition_lines = (
                line.salary_rule_id.account_tax_id.invoice_repartition_line_ids
            )
            tax_lines = repartition_lines.filtered(
                lambda x: x.repartition_type == "tax"
            )
            tax_tag_ids |= tax_lines.mapped("tag_ids")

        return [(6, 0, tax_tag_ids.ids)]

    def _get_tax_repartition_line_id(self, line, account_id):
        if line.salary_rule_id.account_tax_id:
            return (
                self.env["account.tax.repartition.line"]
                .search(
                    [
                        ("invoice_tax_id", "=", line.salary_rule_id.account_tax_id.id),
                        ("account_id", "=", account_id),
                    ],
                    limit=1,
                )
                .id
            )
        return False

    def _create_move_for_payslip(self, slip):
        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        date = slip.date or slip.date_to
        currency = slip.company_id.currency_id or slip.journal_id.company_id.currency_id

        name = _("Payslip of %s") % (slip.employee_id.name)
        move_dict = {
            "narration": name,
            "ref": slip.number,
            "journal_id": slip.journal_id.id,
            "date": date,
        }

        for line in slip.line_ids:
            amount = currency.round(slip.credit_note and -line.total or line.total)
            if currency.is_zero(amount):
                continue
            debit_account_id = line.salary_rule_id.account_debit.id
            credit_account_id = line.salary_rule_id.account_credit.id

            if debit_account_id:
                debit_line = self._prepare_line_values(
                    line, slip, date, debit_account_id, amount, "debit"
                )
                line_ids.append(debit_line)
                debit_sum += debit_line[2]["debit"] - debit_line[2]["credit"]

            if credit_account_id:
                credit_line = self._prepare_line_values(
                    line, slip, date, credit_account_id, amount, "credit"
                )
                line_ids.append(credit_line)
                credit_sum += credit_line[2]["credit"] - credit_line[2]["debit"]

        # Add adjustment entry if needed
        adjust_line = self._prepare_adjustment_entry(slip, date, debit_sum, credit_sum)
        if adjust_line:
            line_ids.append(adjust_line)

        # Create and post move
        if line_ids:
            move_dict["line_ids"] = line_ids
            move = self.env["account.move"].create(move_dict)
            slip.write({"move_id": move.id, "date": date})
            move.action_post()
        else:
            logger.warning(
                f"Payslip {slip.number} did not generate any account move lines"
            )

    def _prepare_line_values(self, line, slip, date, account_id, amount, line_type):
        return (
            0,
            0,
            {
                "name": line.name,
                "partner_id": line._get_partner_id(
                    account_id == line.salary_rule_id.account_credit.id
                )
                or slip.employee_id.address_home_id.id,
                "account_id": account_id,
                "journal_id": slip.journal_id.id,
                "date": date,
                "debit": amount > 0.0 and amount or 0.0
                if line_type == "debit"
                else amount < 0.0 and -amount or 0.0,
                "credit": amount < 0.0 and -amount or 0.0
                if line_type == "debit"
                else amount > 0.0 and amount or 0.0,
                "analytic_account_id": line.salary_rule_id.analytic_account_id.id
                or slip.contract_id.analytic_account_id.id,
                "tax_line_id": line.salary_rule_id.account_tax_id.id,
                "tax_ids": [(4, tax.id, 0) for tax in line.salary_rule_id.tax_line_ids],
                "tax_tag_ids": self._get_tax_tag_ids(line),
                "tax_repartition_line_id": self._get_tax_repartition_line_id(
                    line, account_id
                ),
            },
        )

    def _prepare_adjustment_entry(self, slip, date, debit_sum, credit_sum):
        currency = slip.company_id.currency_id or slip.journal_id.company_id.currency_id

        if currency.compare_amounts(credit_sum, debit_sum) == -1:
            acc_id = slip.journal_id.default_account_id.id
            if not acc_id:
                raise UserError(
                    _(
                        """The Journal '%s' hasn't properly configured the Credit Account!"""
                    )
                    % (slip.journal_id.name)
                )
            return (
                0,
                0,
                {
                    "name": _("Adjustment Entry"),
                    "partner_id": False,
                    "account_id": acc_id,
                    "journal_id": slip.journal_id.id,
                    "date": date,
                    "debit": 0.0,
                    "credit": currency.round(debit_sum - credit_sum),
                },
            )
        elif currency.compare_amounts(debit_sum, credit_sum) == -1:
            acc_id = slip.journal_id.default_account_id.id
            if not acc_id:
                raise UserError(
                    _(
                        """The Journal '%s' hasn't properly configured the Debit Account!"""
                    )
                    % (slip.journal_id.name)
                )
            return (
                0,
                0,
                {
                    "name": _("Adjustment Entry"),
                    "partner_id": False,
                    "account_id": acc_id,
                    "journal_id": slip.journal_id.id,
                    "date": date,
                    "debit": currency.round(credit_sum - debit_sum),
                    "credit": 0.0,
                },
            )
        return None
