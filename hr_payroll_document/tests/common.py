import base64
import contextlib
from unittest import mock

from odoo.tests import common
from odoo.tools.misc import file_path as open_file_path

from odoo.addons.mail.tests.common import mail_new_test_user


class TestHrPayrollDocument(common.TransactionCase):
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

        cls.wizard = cls._create_wizard("January", "hr_payroll_document/tests/test.pdf")

    @classmethod
    def _create_wizard(cls, subject, file_path):
        with open(open_file_path(file_path), "rb") as pdf_file:
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
        cls.subject = subject
        return cls.env["payroll.management.wizard"].create(
            {"payrolls": [cls.attachment.id], "subject": cls.subject}
        )

    @contextlib.contextmanager
    def _mock_valid_identification(self, employee, identification_code):
        def _mocked_validate_payroll_identification(self, code=None):
            if code is None:
                code = employee.identification_id
            return code == identification_code

        with mock.patch.object(
            type(employee),
            "_validate_payroll_identification",
            _mocked_validate_payroll_identification,
        ) as patch:
            patch.side_effect = _mocked_validate_payroll_identification
            yield

    def fill_company_id(self):
        self.env.company.country_id = self.env["res.country"].search(
            [("name", "=", "Spain")]
        )
