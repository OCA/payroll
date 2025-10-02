from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    payroll_fiscalyear_creation_months_before = fields.Integer(
        string="Months Before HR Fiscal Year Creation",
        default=1,
        help="How many months before the end of the HR fiscal year "
        "a new one should be created.",
    )

    @api.constrains("payroll_fiscalyear_creation_months_before")
    def _check_fiscalyear_creation_months_before(self):
        for company in self:
            if (
                company.payroll_fiscalyear_creation_months_before < 0
                or company.payroll_fiscalyear_creation_months_before > 12
            ):
                raise ValidationError(
                    _(
                        "Payroll fiscal year creation months before must be between 0 and 12."
                    )
                )
