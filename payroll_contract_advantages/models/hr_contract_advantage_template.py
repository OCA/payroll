# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

DEFAULT_PYTHON_CODE = """# Available variables:
#  - advantage: the hr.contract.advantage record
#  - contract: the related hr.contract record
#  - employee: the related hr.employee record
#  - payslip: the hr.payslip being computed (None outside a payslip)
# Assign the amount to: result
# E.g. result = contract.wage * 0.05\n\n\n"""


class HrContractAdvandageTemplate(models.Model):
    _name = "hr.contract.advantage.template"
    _description = "Employee's Advantage on Contract"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    lower_bound = fields.Float(help="Lower bound authorized for this advantage")
    upper_bound = fields.Float(help="Upper bound authorized for this advantage")
    default_value = fields.Float()

    # Default "fixed" keeps the historical behaviour (amount =
    # default_value), so existing databases are unaffected.
    computation_mode = fields.Selection(
        selection=[
            ("fixed", "Fixed value"),
            ("percentage", "Percentage of a contract field"),
            ("python", "Python code"),
        ],
        default="fixed",
        required=True,
        help="How the unit value is computed.",
    )
    percentage = fields.Float(help="Percentage applied to the base field.")
    percentage_base = fields.Char(
        string="Percentage Base Field",
        help="Name of a numeric hr.contract field used as base "
        "(e.g. 'wage'). Unknown fields evaluate to 0.",
    )
    python_code = fields.Text(
        default=DEFAULT_PYTHON_CODE,
        help="Python code; assign the amount to 'result'. "
        "Available variables are listed in the field.",
    )
