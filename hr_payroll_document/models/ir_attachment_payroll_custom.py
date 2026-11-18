from odoo import api, fields, models


class IRAttachmentPayrollCustom(models.Model):
    _name = "ir.attachment.payroll.custom"
    _description = "Payroll attachment"
    _rec_name = "subject"

    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Attachment File",
        prefetch=False,
        ondelete="cascade",
    )
    employee_id = fields.Many2one(comodel_name="hr.employee")
    employee = fields.Char(
        string="Employee Name", compute="_compute_employee_details", store=True
    )
    identification_id = fields.Char(compute="_compute_employee_details", store=True)
    create_date = fields.Date(default=fields.Date.context_today)
    subject = fields.Char()

    @api.depends("employee_id")
    def _compute_employee_details(self):
        for payroll_att in self:
            employee = payroll_att.employee_id
            payroll_att.employee = employee.name
            payroll_att.identification_id = employee.identification_id

    def download(self):
        return {
            "type": "ir.actions.act_url",
            "url": "web/content/" + str(self.attachment_id.id) + "/?download=True",
        }
