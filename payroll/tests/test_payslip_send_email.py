# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from .common import TestPayslipBase


class TestPayslipSendEmail(TestPayslipBase):
    def test_payslip_email_template_recipients(self):
        self.richard_emp.work_email = "richard@example.com"
        payslip = self.Payslip.create({"employee_id": self.richard_emp.id})
        template = self.env.ref("payroll.mail_template_hr_payslip")
        self.assertFalse(template.use_default_to)

        composer = (
            self.env["mail.compose.message"]
            .with_context(
                default_composition_mode="mass_mail",
                default_model="hr.payslip",
                default_res_ids=payslip.ids,
                default_template_id=template.id,
            )
            .create({})
        )
        values = composer._prepare_mail_values(payslip.ids)[payslip.id]

        self.assertIn(
            (4, self.richard_emp.work_contact_id.id),
            values["recipient_ids"],
            "The payslip email must be sent to the employee work contact",
        )
        self.assertTrue(values["email_from"], "The sender must not be empty")
