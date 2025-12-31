import base64
import io

import pypdf

from odoo import _
from odoo.exceptions import UserError, ValidationError
from odoo.tests import common
from odoo.tools.misc import file_path

from odoo.addons.mail.tests.common import mail_new_test_user


class TestHRPayrollDocument(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.tz = "Europe/Brussels"
        cls.user_admin = cls.env.ref("base.user_admin")

        # Fix Company without country
        cls.env.company.country_id = False

        # Test users to use through the various tests
        cls.user_employee = mail_new_test_user(
            cls.env, login="david", groups="base.group_user"
        )
        cls.user_employee_id = cls.user_employee.id

        # Hr Data
        cls.employee_emp = cls.env["hr.employee"].create(
            {
                "name": "David Employee",
                "user_id": cls.user_employee_id,
                "company_id": 1,
                "identification_id": "30831011V",
            }
        )

        with open(file_path("hr_payroll_document/tests/test.pdf"), "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read())
        ir_values = {
            "name": "test",
            "type": "binary",
            "datas": encoded_string,
            "store_fname": encoded_string,
            "res_model": "payroll.management.wizard",
            "res_id": 1,
        }
        cls.attachment = cls.env["ir.attachment"].create(ir_values)
        cls.subject = "January"
        cls.wizard = cls.env["payroll.management.wizard"].create(
            {"payrolls": [cls.attachment.id], "subject": cls.subject}
        )

    def fill_company_id(self):
        self.env.company.country_id = self.env["res.country"].search(
            [("name", "=", "Spain")]
        )

    def test_extension_error(self):
        with open(file_path("hr_payroll_document/tests/test.docx"), "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read())
        ir_values = {
            "name": "test",
            "type": "binary",
            "datas": encoded_string,
            "store_fname": encoded_string,
            "res_model": "payroll.management.wizard",
            "res_id": 1,
        }
        self.attachment = self.env["ir.attachment"].create(ir_values)
        self.subject = "January"
        self.wizard = self.env["payroll.management.wizard"].create(
            {"payrolls": [self.attachment.id], "subject": self.subject}
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
