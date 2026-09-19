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
    # per contract. Default "fixed" + the stored amount reproduces the
    # historical behaviour.
    computation_mode = fields.Selection(
        selection=[
            ("fixed", "Fixed value"),
            ("percentage", "Percentage of a contract field"),
            ("python", "Python code"),
        ],
        default="fixed",
        required=True,
    )
    percentage = fields.Float(help="Percentage applied to the base field.")
    percentage_base = fields.Char(
        string="Percentage Base Field",
        help="Name of a numeric hr.contract field used as base "
        "(e.g. 'wage'). Unknown fields evaluate to 0.",
    )
    python_code = fields.Text(
        help="Python code; assign the amount to 'result'. "
        "Available variables are listed in the field.",
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
        help="Python code; assign the quantity to 'result'. "
        "Available variables are listed in the field.",
    )
    amount = fields.Float(
        string="Unit amount",
        help="Unit value. Recomputed per payslip for non-fixed modes; "
        "the final amount is this value times the quantity.",
    )
    quantity_final = fields.Float(
        string="Computed Quantity",
        compute="_compute_quantity_final",
        help="Quantity actually applied (preview; recomputed on the "
        "payslip for period-sensitive formulas).",
    )

    @api.onchange("advantage_template_id")
    def _onchange_advantage_template_id(self):
        """Copy the template definition onto the advantage.

        In 'fixed' mode ``amount`` keeps coming from the template
        default value (historical behaviour). In 'percentage'/'python'
        mode it is previewed from the actual computation so the user
        does not see 0 while configuring; bounds are still enforced by
        the ``amount`` constraint on save. Payslips recompute it live.
        """
        for record in self:
            template = record.advantage_template_id
            if not template:
                continue
            record.computation_mode = template.computation_mode
            record.percentage = template.percentage
            record.percentage_base = template.percentage_base
            record.python_code = template.python_code
            record.quantity_mode = template.quantity_mode
            record.quantity_fixed_value = template.quantity_fixed_value
            record.quantity_python_code = template.quantity_python_code
            if record.computation_mode == "fixed":
                record.amount = template.default_value
            else:
                preview, warning = record._preview_unit_value()
                record.amount = preview
                if warning:
                    return warning

    @api.onchange(
        "computation_mode",
        "percentage",
        "percentage_base",
        "python_code",
    )
    def _onchange_computation_preview(self):
        """Preview ``amount`` while configuring the line.

        Only in 'percentage'/'python' mode; 'fixed' keeps the
        user-entered amount. Bounds are enforced by the ``amount``
        constraint on save and payslips recompute it live.
        """
        for record in self:
            if record.computation_mode and record.computation_mode != "fixed":
                preview, warning = record._preview_unit_value()
                record.amount = preview
                if warning:
                    return warning

    def _preview_unit_value(self):
        """Tolerant unit value for the configuration screen.

        Returns (value, warning). On any evaluation error the value is
        0.0 and a non-blocking warning carries the exception text, so
        the user can keep configuring without a traceback dialog. The
        payslip computation stays strict.
        """
        self.ensure_one()
        try:
            return self._compute_unit_value(), None
        except Exception as err:
            warning = {
                "warning": {
                    "title": _("Preview unavailable"),
                    "message": _(
                        "The amount could not be evaluated; set to 0. "
                        "It will be recomputed on the payslip.\n\n%s"
                    )
                    % err,
                }
            }
            return 0.0, warning

    def _compute_advantage_amount(self, payslip=None):
        """Return the final amount (unit value x quantity), bounded.

        Evaluated per payslip. Bounds are enforced on the final amount.

        :param payslip: optional hr.payslip, exposed to python formulas.
        """
        self.ensure_one()
        unit_value = self._compute_unit_value(payslip=payslip)
        quantity = self._compute_quantity(payslip=payslip)
        amount = unit_value * quantity
        self._check_bounds(amount)
        return amount

    def _compute_unit_value(self, payslip=None):
        """Unit value per the computation mode."""
        self.ensure_one()
        contract = self.contract_id
        mode = self.computation_mode or "fixed"

        if mode == "fixed":
            # Backward compatibility: the amount is typed directly on
            # the advantage, so existing flows/records are unaffected.
            value = self.amount
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

    @api.depends(
        "quantity_mode",
        "quantity_fixed_value",
        "quantity_python_code",
    )
    def _compute_quantity_final(self):
        """Tolerant quantity preview for lists/forms.

        Never raises so the list always renders; the payslip recomputes
        it strictly with the period context.
        """
        for record in self:
            try:
                record.quantity_final = record._compute_quantity()
            except Exception:
                record.quantity_final = 0.0

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
        """Enforce template bounds on the final amount (unit x qty)."""
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
