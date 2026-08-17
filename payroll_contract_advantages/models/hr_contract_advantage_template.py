# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrContractAdvandageTemplate(models.Model):
    _name = "hr.contract.advantage.template"
    _description = "Employee's Advantage on Contract"

    _sql_constraints = [
        (
            "code_unique",
            "unique(code)",
            "The code must be unique per advantage template: it is used to "
            "reference the advantage from salary rules and payslip lines.",
        )
    ]

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    lower_bound = fields.Float(
        digits="Payroll",
        help="Lower bound authorized by the employer for this advantage. "
        "Leave at 0 for no lower bound.",
    )
    upper_bound = fields.Float(
        digits="Payroll",
        help="Upper bound authorized by the employer for this advantage. "
        "Leave at 0 for no upper bound.",
    )
    default_value = fields.Float(digits="Payroll")

    @api.constrains("lower_bound", "upper_bound", "default_value")
    def _check_bounds_consistency(self):
        for template in self:
            # 0.0 means "no bound on that side", matching
            # hr.contract.advantage._check_bound_limits().
            if (
                template.lower_bound
                and template.upper_bound
                and template.lower_bound > template.upper_bound
            ):
                raise ValidationError(
                    _("Lower bound can't be greater than upper bound.")
                )
            if template.upper_bound and template.default_value > template.upper_bound:
                raise ValidationError(
                    _("Default value can't be greater than upper bound.")
                )
            if (
                template.lower_bound
                and template.default_value
                and template.default_value < template.lower_bound
            ):
                raise ValidationError(
                    _("Default value can't be less than lower bound.")
                )
