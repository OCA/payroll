# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, api, exceptions, fields, models
from odoo.tools.misc import flatten

from odoo.addons.queue_job.job import CANCELLED, DONE, FAILED


class PayrollManagamentWizard(models.TransientModel):
    _inherit = "payroll.management.wizard"

    is_payroll_being_processed = fields.Boolean(
        string="Is being processed",
        help="One of the selected payrolls is being processed.",
        compute="_compute_is_payroll_being_processed",
        compute_sudo=True,
    )
    is_send_visible = fields.Boolean(
        string="Send button is visible",
        compute="_compute_is_send_visible",
    )

    def _notify_async_processed(self, send_result):
        """Notify the result to the user that processed the payrolls."""
        self.ensure_one()
        odoobot = self.env.ref("base.partner_root")
        user = self.env.user
        return self.env["mail.thread"].message_notify(
            author_id=odoobot.id,
            partner_ids=user.partner_id.ids,
            subject=send_result["params"]["title"],
            body=send_result["params"]["message"],
            model=self._name,
            res_id=self.id,
        )

    def send_payrolls(self):
        if not self.is_send_visible:
            # We are already hiding the buttons in the UI,
            # but this public method can still be executed.
            raise exceptions.UserError(_("The selected payrolls cannot be processed."))

        result = super().send_payrolls()

        if self.env.context.get("job_uuid"):
            self._notify_async_processed(result)
        return result

    def send_payrolls_async(self):
        return self.with_delay().send_payrolls()

    def _get_payrolls_being_processed(self):
        jobs = self.env["queue.job"].search(
            [
                ("model_name", "=", self._name),
                ("method_name", "=", "send_payrolls"),
                ("state", "not in", [CANCELLED, DONE, FAILED]),
            ]
        )
        jobs_records_ids = [
            wizard_id
            for wizard_id in flatten(jobs.mapped("record_ids"))
            if wizard_id not in self.ids
        ]
        jobs_records = self.browse(jobs_records_ids).exists()
        return jobs_records.payrolls

    @api.depends(
        "payrolls",
    )
    def _compute_is_payroll_being_processed(self):
        jobs_payrolls_checksums = set(
            self._get_payrolls_being_processed().mapped("checksum")
        )

        for wizard in self:
            wizard.is_payroll_being_processed = any(
                payroll.checksum in jobs_payrolls_checksums
                for payroll in wizard.payrolls
            )

    @api.depends(
        "is_payroll_being_processed",
    )
    def _compute_is_send_visible(self):
        for wizard in self:
            wizard.is_send_visible = not wizard.is_payroll_being_processed
