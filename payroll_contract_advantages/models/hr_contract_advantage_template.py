# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


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
        help="Numeric hr.contract field used as base (e.g. 'wage').",
    )
    python_code = fields.Text(
        help="Expression with: advantage, contract, employee, payslip. "
        "Set 'result'. E.g. result = contract.wage * 0.05",
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
        help="Expression with: advantage, contract, employee, payslip. "
        "Set 'result'.",
    )
