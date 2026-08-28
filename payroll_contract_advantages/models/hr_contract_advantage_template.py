# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

DEFAULT_PYTHON_CODE = """# Available variables:
#  - advantage: the hr.contract.advantage record
#  - contract: the related hr.contract record
#  - employee: the related hr.employee record
#  - payslip: the hr.payslip being computed (None outside a payslip)
# Assign the amount to: result
# E.g. result = contract.wage * 0.05\n\n\n"""

DEFAULT_QUANTITY_PYTHON_CODE = """# Available variables:
#  - advantage: the hr.contract.advantage record
#  - contract: the related hr.contract record
#  - employee: the related hr.employee record
#  - payslip: the hr.payslip being computed (None outside a payslip)
# Assign the quantity to: result
# E.g. sum the worked days of the current payslip:
# result = sum(payslip.worked_days_line_ids.mapped("number_of_days"))\n\n\n"""


class HrContractAdvandageTemplate(models.Model):
    _name = "hr.contract.advantage.template"
    _description = "Employee's Advantage on Contract"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    lower_bound = fields.Float(
        help="Lower bound enforced on the final amount " "(unit value x quantity)."
    )
    upper_bound = fields.Float(
        help="Upper bound enforced on the final amount " "(unit value x quantity)."
    )
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

    # Final amount = quantity * unit value. Default fixed quantity 1.0
    # keeps the historical behaviour (amount = unit value).
    quantity_mode = fields.Selection(
        selection=[
            ("fixed", "Fixed quantity"),
            ("python", "Python code"),
        ],
        default="fixed",
        required=True,
        help="How the quantity is computed.",
    )
    quantity_fixed_value = fields.Float(
        string="Quantity",
        default=1.0,
        help="Quantity used in 'Fixed quantity' mode.",
    )
    quantity_python_code = fields.Text(
        default=DEFAULT_QUANTITY_PYTHON_CODE,
        help="Python code; assign the quantity to 'result'. "
        "Available variables are listed in the field.",
    )
