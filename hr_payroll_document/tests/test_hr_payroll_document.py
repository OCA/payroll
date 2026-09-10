import base64
import io

import pypdf

from odoo import _
from odoo.exceptions import UserError, ValidationError

from odoo.addons.hr_payroll_document.tests.common import TestHrPayrollDocument


class TestHRPayrollDocument(TestHrPayrollDocument):
    def test_extension_error(self):
        self.wizard = self._create_wizard(
            "January", "hr_payroll_document/tests/test.docx"
        )
        with self.assertRaises(ValidationError):
            self.wizard.send_payrolls()

    def test_company_id_required(self):
        with self.assertRaises(UserError):
            self.wizard.send_payrolls()

    def test_employee_vat_not_valid(self):
        self.fill_company_id()
        with self.assertRaises(ValidationError):
            employees = self.env["hr.employee"].search([])
            for employee in employees:
                if not employee.identification_id:
                    employee.identification_id = "XXXXXXX"

    def test_one_employee_not_found(self):
        self.fill_company_id()
        self.env["hr.employee"].search([("id", "=", 1)]).identification_id = "37936636E"
        self.assertEqual(
            self.wizard.send_payrolls()["params"]["title"], _("Employees not found")
        )
        self.assertEqual(
            self.wizard.send_payrolls()["params"]["message"],
            _("IDs whose employee has not been found: ") + "51000278D",
        )

    def test_send_payrolls_correctly(self):
        self.fill_company_id()
        self.env["hr.employee"].search([("id", "=", 1)]).identification_id = "51000278D"
        self.assertEqual(
            self.wizard.send_payrolls()["params"]["title"], _("Payrolls sent")
        )
        self.assertEqual(
            self.wizard.send_payrolls()["params"]["message"],
            _("Payrolls sent to employees correctly"),
        )

    def test_optional_encryption(self):
        """The employee's payroll can be not encrypted."""
        # Arrange
        self.fill_company_id()
        employee = self.employee_emp
        employee.update(
            {
                "identification_id": "51000278D",
                "no_payroll_encryption": True,
            }
        )
        # pre-condition
        self.assertTrue(employee.no_payroll_encryption)

        # Act
        self.wizard.send_payrolls()

        # Assert
        payroll = (
            self.env["ir.attachment.payroll.custom"]
            .search(
                [
                    ("identification_id", "=", employee.identification_id),
                ]
            )
            .attachment_id
        )
        self.assertTrue(payroll)
        payroll_content = base64.b64decode(payroll.datas)
        payroll_pdf = pypdf.PdfReader(io.BytesIO(payroll_content))
        self.assertFalse(payroll_pdf.is_encrypted)

    def test_attachment_name_has_pdf_extension(self):
        """Payroll attachments must be sent with a .pdf extension."""
        # Arrange
        self.fill_company_id()
        employee = self.employee_emp
        employee.identification_id = "51000278D"

        # Act
        self.wizard.send_payrolls()

        # Assert
        payroll = (
            self.env["ir.attachment.payroll.custom"]
            .search([("identification_id", "=", employee.identification_id)])
            .attachment_id
        )
        self.assertTrue(payroll.name.endswith(".pdf"))

    def test_optional_encryption_fetch(self):
        """If the user can't access the employees,
        the optional encryption field is not fetched."""
        # Arrange
        employee = self.employee_emp
        employee_with_self = employee.with_user(employee.user_id)
        # pre-condition
        self.assertFalse(
            employee_with_self.check_access_rights("read", raise_exception=False)
        )

        # Assert: reading a field triggers fetching all the accessible fields
        employee_with_self.invalidate_recordset()
        self.assertTrue(employee_with_self.user_id)
