# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class HrContractAdvantage(models.Model):
    _name = "hr.contract.advantage"
    _description = "Employee's Advantages on Contract"

    contract_id = fields.Many2one("hr.contract")
    advantage_template_id = fields.Many2one(
        "hr.contract.advantage.template", string="Advantage Template"
    )
    advantage_template_code = fields.Char(
        string="Code", related="advantage_template_id.code", readonly=True
    )
    advantage_lower_bound = fields.Float(
        string="Lower Bound", related="advantage_template_id.lower_bound", readonly=True
    )
    advantage_upper_bound = fields.Float(
        string="Upper Bound", related="advantage_template_id.upper_bound", readonly=True
    )

    # Definition copied from the template on selection, then editable
    # per contract. Default "fixed" + fixed_value reproduces the
    # historical amount behaviour (see migration).
    computation_mode = fields.Selection(
        selection=[
            ("fixed", "Fixed value"),
            ("percentage", "Percentage of a contract field"),
            ("python", "Python code"),
        ],
        default="fixed",
        required=True,
    )
    fixed_value = fields.Float(help="Value used in 'Fixed value' mode.")
    percentage = fields.Float(help="Percentage applied to the base field.")
    percentage_base = fields.Char(
        string="Percentage Base Field",
        help="Numeric hr.contract field used as base (e.g. 'wage').",
    )
    python_code = fields.Text(
        help="Expression with: advantage, contract, employee, payslip. "
        "Set 'result'.",
    )
    quantity_mode = fields.Selection(
        selection=[
            ("fixed", "Fixed quantity"),
            ("python", "Python code"),
        ],
        default="fixed",
        required=True,
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
    amount = fields.Float(
        help="Latest evaluated amount (quantity x unit value), "
        "recomputed per payslip for non-fixed modes."
    )

    @api.onchange("advantage_template_id")
    def _onchange_advantage_template_id(self):
        """Copy the template definition onto the advantage.

        ``amount`` is still populated from the template default value so
        existing flows and the 'fixed' mode behave as before.
        """
        for record in self:
            template = record.advantage_template_id
            if not template:
                continue
            record.computation_mode = template.computation_mode
            record.fixed_value = template.default_value
            record.percentage = template.percentage
            record.percentage_base = template.percentage_base
            record.python_code = template.python_code
            record.quantity_mode = template.quantity_mode
            record.quantity_fixed_value = template.quantity_fixed_value
            record.quantity_python_code = template.quantity_python_code
            record.amount = template.default_value

    def _compute_advantage_amount(self, payslip=None):
        """Return quantity x unit value, bounded. Evaluated per payslip.

        :param payslip: optional hr.payslip, exposed to python formulas.
        """
        self.ensure_one()
        unit_value = self._compute_unit_value(payslip=payslip)
        quantity = self._compute_quantity(payslip=payslip)
        amount = quantity * unit_value
        self._check_bounds(amount)
        return amount

    def _compute_unit_value(self, payslip=None):
        """Unit value per the computation mode."""
        self.ensure_one()
        contract = self.contract_id
        mode = self.computation_mode or "fixed"

        if mode == "fixed":
            # Backward compatibility: historically the amount was typed
            # directly on the advantage (no fixed_value field). If
            # fixed_value was never set but amount was, keep using
            # amount so existing flows/records are unaffected.
            if not self.fixed_value and self.amount:
                value = self.amount
            else:
                value = self.fixed_value
        elif mode == "percentage":
            base_field = (self.percentage_base or "").strip()
            base_value = 0.0
            if base_field and contract:
                base_value = contract[base_field] if base_field in contract else 0.0
            value = (base_value or 0.0) * (self.percentage or 0.0) / 100.0
        elif mode == "python":
            value = self._eval_code(self.python_code, payslip=payslip)
        else:
            value = 0.0

        return self._coerce_float(value, _("unit value"))

    def _compute_quantity(self, payslip=None):
        """Quantity per the quantity mode. Default fixed 1.0."""
        self.ensure_one()
        mode = self.quantity_mode or "fixed"
        if mode == "python":
            value = self._eval_code(self.quantity_python_code, payslip=payslip)
        else:
            # An explicit 0 quantity is valid (amount 0).
            value = (
                self.quantity_fixed_value
                if self.quantity_fixed_value is not False
                else 1.0
            )
        return self._coerce_float(value, _("quantity"))

    def _coerce_float(self, value, label):
        """Float guarantee, mirroring hr.salary.rule._compute_rule."""
        try:
            return float(value)
        except (TypeError, ValueError) as err:
            raise UserError(
                _(
                    "The computed %(label)s of advantage "
                    "'%(advantage)s' must be a float."
                )
                % {
                    "label": label,
                    "advantage": self.advantage_template_id.name
                    or self.advantage_template_code
                    or self.id,
                }
            ) from err

    def _eval_code(self, code, payslip=None):
        """Safely evaluate a generic python expression."""
        self.ensure_one()
        if not code:
            return 0.0
        localdict = {
            "advantage": self,
            "contract": self.contract_id,
            "employee": self.contract_id.employee_id
            if self.contract_id
            else self.env["hr.employee"],
            "payslip": payslip,
            "result": 0.0,
        }
        safe_eval(code, localdict, mode="exec", nocopy=True)
        return localdict.get("result", 0.0) or 0.0

    def _check_bounds(self, value):
        """Enforce template lower/upper bounds on a candidate amount."""
        self.ensure_one()
        if value and value != 0.00:
            if self.advantage_upper_bound and value > self.advantage_upper_bound:
                raise ValidationError(
                    _("Advantage amount can't be greater than upper bound limit.")
                )
            elif self.advantage_lower_bound and value < self.advantage_lower_bound:
                raise ValidationError(
                    _("Advantage amount can't be less than lower bound limit.")
                )

    @api.constrains("amount")
    def _check_bound_limits(self):
        for record in self:
            record._check_bounds(record.amount)
