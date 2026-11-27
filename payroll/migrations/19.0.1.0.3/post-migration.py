# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import SUPERUSER_ID, api

OLD_SENDER = "{{user.employee_id.work_email}}"
NEW_SENDER = "{{ user.employee_id.work_email or user.email_formatted }}"


def migrate(cr, version):
    """Fix the payslip mail template on existing databases.

    The template is declared in a noupdate block, so the XML changes are not
    applied on update. Disable default recipients so the template email_to is
    used, and update the sender only if it was not customized.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    template = env.ref("payroll.mail_template_hr_payslip", raise_if_not_found=False)
    if not template:
        return
    vals = {"use_default_to": False}
    if template.email_from == OLD_SENDER:
        vals["email_from"] = NEW_SENDER
    if template.reply_to == OLD_SENDER:
        vals["reply_to"] = NEW_SENDER
    template.write(vals)
