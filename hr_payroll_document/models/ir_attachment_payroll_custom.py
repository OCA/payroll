from odoo import fields, models


class IRAttachmentPayrollCustom(models.Model):
    _name = "ir.attachment.payroll.custom"
    _description = "Payroll attachment"

    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Attachment File",
        prefetch=False,
        ondelete="cascade",
    )
    employee = fields.Char()
    identification_id = fields.Char("Identification ID")
    create_date = fields.Date(default=fields.Date.context_today)
    subject = fields.Char()

    def download(self):
        return {
            "type": "ir.actions.act_url",
            "url": "web/content/" + str(self.attachment_id.id) + "/?download=True",
        }
