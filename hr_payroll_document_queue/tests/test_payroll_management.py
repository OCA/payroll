# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import exceptions

from odoo.addons.hr_payroll_document.tests.common import TestHrPayrollDocument
from odoo.addons.mail.tests.common import MailCase
from odoo.addons.queue_job.tests.common import trap_jobs


class TestPayrollManagement(MailCase, TestHrPayrollDocument):
    def test_job_creation(self):
        """The job is created."""
        # Arrange
        self.fill_company_id()
        employee = self.employee_emp
        employee.identification_id = "51000278D"

        # Act
        with trap_jobs() as trap:
            self.wizard.send_payrolls_async()

        # Assert
        trap.assert_jobs_count(1)

    def test_process_same_payroll(self):
        """The same payroll cannot be processed if it is already being processed."""
        # Arrange
        self.fill_company_id()
        self.employee_emp.identification_id = "51000278D"
        self.wizard.send_payrolls_async()
        other_wizard = self.wizard.copy()
        other_wizard.payrolls = self.wizard.payrolls

        # Act
        with self.assertRaises(exceptions.UserError) as ue:
            other_wizard.send_payrolls()

        # Assert
        exc_message = ue.exception.args[0]
        self.assertIn("cannot be processed", exc_message)
        self.assertTrue(other_wizard.is_payroll_being_processed)
        self.assertFalse(other_wizard.is_send_visible)

    def test_email_notification(self):
        """
        If the user has "email" notification preference,
        when the payrolls are processed the user is notified.
        """
        # Arrange
        self.fill_company_id()
        employee = self.employee_emp
        employee.identification_id = "51000278D"
        author_partner = self.env.ref("base.partner_root")
        payman_user = self.user_admin
        payman_user.notification_type = "email"
        wizard = self.wizard

        # Act
        with trap_jobs() as trap, self.mock_mail_gateway():
            wizard.with_user(payman_user).send_payrolls_async()
            trap.perform_enqueued_jobs()

        # Assert
        email = self.assertMailMail(
            payman_user.partner_id,
            "sent",
            author=author_partner,
        )
        self.assertEqual(email.model, wizard._name)
        self.assertEqual(email.res_id, wizard.id)
