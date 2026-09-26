from odoo import fields, models


class Attachment(models.Model):
    _inherit = "ir.attachment"

    payrol_rel = fields.Many2many(
        "payroll.management.wizard",
        "payrolls",
        "attachment_id3",
        "document_id",
        string="Attachment",
    )
    document_type = fields.Selection([("payroll", "Payroll")])
