import base64
from base64 import b64decode

from pypdf import PdfReader, PdfWriter, errors

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError


class PayrollManagamentWizard(models.TransientModel):
    _name = "payroll.management.wizard"
    _description = "Payroll Management"

    subject = fields.Char(
        help="Enter the title of the payroll whether it is the month, week, day, etc.",
        required=True,
    )
    payrolls = fields.Many2many(
        "ir.attachment", "payrol_rel", "doc_id", "attach_id3", copy=False, required=True
    )

    def _get_fallback_reader(self, pdf_reader):
        # Override to use another reader
        pass

    def _read_page_content(self, pdf_reader, page, fallback_reader=None):
        try:
            page_content = page.extract_text().split()
        except errors.PdfReadError:
            if fallback_reader:
                # The original page cannot be read:
                # read the simplified page in the fallback_reader
                page_number = pdf_reader.get_page_number(page)
                fallback_page = fallback_reader.get_page(page_number)
                page_content = fallback_page.extract_text().split()
            else:
                raise
        return page_content

    def _extract_employees(self, pdf_reader, fallback_reader=None):
        employee_to_pages = dict()
        not_found_ids = set()

        # Find all IDs of the employees
        for page in pdf_reader.pages:
            page_content = self._read_page_content(
                pdf_reader, page, fallback_reader=fallback_reader
            )
            for value in page_content:
                if self.validate_id(value) and value != self.env.company.vat:
                    employee = self.env["hr.employee"].search(
                        [("identification_id", "=", value)]
                    )
                    if employee:
                        employee_to_pages.setdefault(employee, []).append(page)
                    else:
                        not_found_ids.add(value)
                    break

        return employee_to_pages, not_found_ids

    def _build_employee_payroll(self, file_name, pdf_pages, encryption_key=None):
        """Return the path to the created payroll.

        Optionally encrypt the payroll file with `encryption_key`.
        """
        pdfWriter = PdfWriter()
        for page in pdf_pages:
            pdfWriter.add_page(page)

        path = "/tmp/" + file_name

        if encryption_key:
            pdfWriter.encrypt(encryption_key, algorithm="AES-256")

        with open(path, "wb") as f:
            pdfWriter.write(f)
        return path

    def _show_employees_action(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "hr_payroll_document.payrolls_view_action"
        )
        action["views"] = [
            [self.env.ref("hr_payroll_document.view_payroll_tree").id, "list"]
        ]
        return action

    def send_payrolls(self):
        self.merge_pdfs()
        # Validate if company have country
        if not self.env.company.country_id:
            raise UserError(_("You must to filled country field of company"))

        reader = PdfReader("/tmp/merged-pdf.pdf")

        try:
            employee_to_pages, not_found = self._extract_employees(reader)
        except errors.PdfReadError:
            # Couldn't read the file, try again with another reader
            fallback_reader = self._get_fallback_reader(reader)
            if fallback_reader:
                employee_to_pages, not_found = self._extract_employees(
                    reader, fallback_reader=fallback_reader
                )
            else:
                raise

        for employee, pages in employee_to_pages.items():
            encryption_key = (
                None if employee.no_payroll_encryption else employee.identification_id
            )
            path = self._build_employee_payroll(
                _(
                    "Payroll %(subject)s %(employee)s.pdf",
                    employee=employee.name,
                    subject=self.subject,
                ),
                pages,
                encryption_key=encryption_key,
            )
            # Send payroll to the employee
            self.send_mail(employee, path)

        action = self._show_employees_action()
        if not_found:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Employees not found"),
                    "message": _("IDs whose employee has not been found: ")
                    + ", ".join(list(not_found)),
                    "sticky": True,
                    "type": "warning",
                    "next": action,
                },
            }

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Payrolls sent"),
                "message": _("Payrolls sent to employees correctly"),
                "sticky": False,
                "type": "success",
                "next": action,
            },
        }

    def merge_pdfs(self):
        # Merge the pdfs together
        pdfs = []
        for file in self.payrolls:
            b64 = file.datas
            btes = b64decode(b64, validate=True)
            if btes[0:4] != b"%PDF":
                raise ValidationError(_("Missing pdf file signature"))
            f = open("/tmp/" + file.name, "wb")
            f.write(btes)
            f.close()
            pdfs.append(f.name)

        merger = PdfWriter()

        for pdf in pdfs:
            merger.append(pdf)

        merger.write("/tmp/merged-pdf.pdf")
        merger.close()

    def send_mail(self, employee, path):
        # Open Payrolls of employee and encode content
        with open(path, "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read())

        # Attach file to email
        ir_values = {
            "name": _("Payroll") + "_" + self.subject + "_" + employee.name + ".pdf",
            "type": "binary",
            "datas": encoded_string,
            "store_fname": encoded_string,
            "res_model": "hr.employee",
            "res_id": employee.id,
            "document_type": "payroll",
        }

        # Save payroll attachment to all employee payrolls attachments
        self.env["ir.attachment.payroll.custom"].create(
            {
                "attachment_id": self.env["ir.attachment"].create(ir_values).id,
                "employee": employee.name,
                "subject": self.subject,
                "identification_id": employee.identification_id,
            }
        )

        # Send mail
        mail_template = self.env.ref(
            "hr_payroll_document.payroll_employee_email_template"
        )
        data_id = [(6, 0, [self.env["ir.attachment"].create(ir_values).id])]
        mail_template.attachment_ids = data_id
        mail_template.with_context(**{"subject": self.subject}).send_mail(
            employee.id, force_send=True
        )

    def validate_id(self, code):
        return self.env["hr.employee"]._validate_payroll_identification(code=code)
