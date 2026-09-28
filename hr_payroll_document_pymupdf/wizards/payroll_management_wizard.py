# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import io

import pymupdf
import pypdf
from reportlab.pdfgen import canvas

from odoo import models


class PayrollManagamentWizard(models.TransientModel):
    _inherit = "payroll.management.wizard"

    def _get_fallback_reader(self, pdf_reader):
        reader = super()._get_fallback_reader(pdf_reader)
        if not reader:
            # Read the file with another reader
            doc = pymupdf.Document(stream=pdf_reader.stream)

            # Create a new PDF with only the extracted content
            pdf_content = io.BytesIO()
            pdf_canvas = canvas.Canvas(pdf_content)
            for page_number in range(pdf_reader.get_num_pages()):
                page_content = doc[page_number].get_text().split()
                # Create a new page with the read content
                pdf_canvas.drawString(0, 0, " ".join(page_content))
                pdf_canvas.showPage()
            pdf_canvas.save()

            # Return a PyPDF reader for the new PDF,
            # that now is readable
            reader = pypdf.PdfReader(pdf_content)
        return reader
