# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import tools

from odoo.addons.hr_payroll_document.tests.common import TestHrPayrollDocument


class TestPayrollManagement(TestHrPayrollDocument):
    def test_pdf_broken_image(self):
        """If the PDF cannot be processed with PyPDF, try with another reader."""
        self.fill_company_id()
        identification_code = "xXXXXXXXXXXXXXXX"
        with self._mock_valid_identification(self.employee_emp, identification_code):
            self.employee_emp.identification_id = identification_code
        self.wizard = self._create_wizard(
            "Subject", "hr_payroll_document_pymupdf/tests/test_broken_image.pdf"
        )
        with (
            self._mock_valid_identification(self.employee_emp, identification_code),
            tools.mute_logger("pypdf.generic._image_inline"),
        ):
            result_action = self.wizard.send_payrolls()
        self.assertEqual(result_action["params"]["title"], self.env._("Payrolls sent"))
