# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError

from odoo.addons.payroll.tests.common import TestPayslipBase


class TestPayrollContractAdvantages(TestPayslipBase):
    def setUp(self):
        super().setUp()
        self.AdvantageTemplate = self.env["hr.contract.advantage.template"]
        self.Advantage = self.env["hr.contract.advantage"]

    def _create_template(
        self,
        *,
        lower=0.0,
        upper=100.0,
        default=10.0,
        code="BEN",
        name="Benefit",
    ):
        return self.AdvantageTemplate.create(
            {
                "name": name,
                "code": code,
                "lower_bound": lower,
                "upper_bound": upper,
                "default_value": default,
            }
        )

    def test_onchange_advantage_template_sets_default_amount(self):
        """Onchange should set amount from template default value."""
        template = self._create_template(default=123.45)
        advantage = self.Advantage.new(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
            }
        )

        advantage._onchange_advantage_template_id()

        self.assertEqual(advantage.amount, template.default_value)

    def test_constraint_allows_amount_inside_bounds(self):
        """Constraint should allow amount inside bounds."""
        template = self._create_template(lower=0.0, upper=100.0)

        advantage = self.Advantage.create(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
                "amount": 50.0,
            }
        )

        self.assertEqual(advantage.amount, 50.0)

    def test_constraint_raises_if_above_upper_bound(self):
        """Constraint should raise when amount is above upper bound."""
        template = self._create_template(lower=0.0, upper=100.0)

        with self.assertRaises(ValidationError):
            self.Advantage.create(
                {
                    "contract_id": self.richard_contract.id,
                    "advantage_template_id": template.id,
                    "amount": 150.0,
                }
            )

    def test_constraint_raises_if_below_lower_bound(self):
        """Constraint should raise when amount is below lower bound."""
        template = self._create_template(lower=10.0, upper=100.0)

        with self.assertRaises(ValidationError):
            self.Advantage.create(
                {
                    "contract_id": self.richard_contract.id,
                    "advantage_template_id": template.id,
                    "amount": 5.0,
                }
            )

    def test_get_current_contract_dict_contains_advantages(self):
        """get_current_contract_dict should expose advantages by code."""
        template = self._create_template(
            lower=0.0,
            upper=100.0,
            default=25.0,
            code="FUEL",
            name="Fuel Allowance",
        )

        self.Advantage.create(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
                "amount": 30.0,
            }
        )

        self.apply_contract_cron()

        payslip = self.Payslip.create({"employee_id": self.richard_emp.id})
        payslip.onchange_employee()
        contracts = payslip._get_employee_contracts()

        res = payslip.get_current_contract_dict(self.richard_contract, contracts)
        advantages = res.get("advantages")

        self.assertIsNotNone(advantages)
        self.assertEqual(advantages.FUEL, 30.0)

    # ------------------------------------------------------------------
    # Computation modes (enhancement 18.0.2.0.0)
    # ------------------------------------------------------------------

    def test_default_mode_is_fixed_backward_compatible(self):
        """A template created the historical way defaults to 'fixed'."""
        template = self._create_template(default=99.0)
        self.assertEqual(template.computation_mode, "fixed")

        advantage = self.Advantage.new(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
            }
        )
        advantage._onchange_advantage_template_id()
        self.assertEqual(advantage.computation_mode, "fixed")
        self.assertEqual(advantage.fixed_value, 99.0)
        # Historical 'amount' still populated from default value.
        self.assertEqual(advantage.amount, 99.0)

    def test_fixed_mode_amount_equals_fixed_value(self):
        template = self._create_template(default=150.0, upper=1000000.0)
        advantage = self.Advantage.create(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
                "computation_mode": "fixed",
                "fixed_value": 150.0,
                "amount": 150.0,
            }
        )
        self.assertEqual(advantage._compute_advantage_amount(), 150.0)

    def test_percentage_mode_uses_contract_field(self):
        template = self._create_template(
            lower=0.0, upper=1000000.0, code="HOUSING", name="Housing"
        )
        template.computation_mode = "percentage"
        template.percentage = 5.0
        template.percentage_base = "wage"

        advantage = self.Advantage.new(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
            }
        )
        advantage._onchange_advantage_template_id()
        self.assertEqual(advantage.computation_mode, "percentage")
        self.assertEqual(advantage.percentage, 5.0)
        self.assertEqual(advantage.percentage_base, "wage")

        expected = self.richard_contract.wage * 5.0 / 100.0
        self.assertAlmostEqual(advantage._compute_advantage_amount(), expected)

    def test_python_mode_evaluates_formula(self):
        template = self._create_template(
            lower=0.0, upper=1000000.0, code="PY", name="Py"
        )
        template.computation_mode = "python"
        template.python_code = "result = contract.wage * 0.10"

        advantage = self.Advantage.new(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
            }
        )
        advantage._onchange_advantage_template_id()
        expected = self.richard_contract.wage * 0.10
        self.assertAlmostEqual(advantage._compute_advantage_amount(), expected)

    def test_python_mode_receives_payslip_in_localdict(self):
        """The python localdict must expose payslip (needed by
        period-sensitive localisation formulas)."""
        template = self._create_template(
            lower=0.0, upper=1000000.0, code="PYPS", name="PyPayslip"
        )
        template.computation_mode = "python"
        # If payslip is exposed and not None, result is the wage,
        # otherwise 0 -> asserts the name is present in the localdict.
        template.python_code = "result = contract.wage if payslip is not None else 0.0"
        advantage = self.Advantage.new(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
            }
        )
        advantage._onchange_advantage_template_id()

        self.apply_contract_cron()
        payslip = self.Payslip.create({"employee_id": self.richard_emp.id})
        payslip.onchange_employee()
        amount = advantage._compute_advantage_amount(payslip=payslip)
        self.assertAlmostEqual(amount, self.richard_contract.wage)

    def test_bounds_enforced_on_computed_amount(self):
        """Bounds must be checked on the evaluated amount, not only on
        a manually typed one."""
        template = self._create_template(
            lower=0.0, upper=100.0, code="CAP", name="Capped"
        )
        template.computation_mode = "python"
        template.python_code = "result = 500.0"  # above upper bound

        advantage = self.Advantage.new(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
            }
        )
        advantage._onchange_advantage_template_id()
        with self.assertRaises(ValidationError):
            advantage._compute_advantage_amount()

    def test_get_current_contract_dict_evaluates_percentage(self):
        """End to end: the value exposed to salary rules is the
        evaluated formula, recomputed at payslip time."""
        template = self._create_template(
            lower=0.0, upper=1000000.0, code="PCT", name="Pct"
        )
        template.computation_mode = "percentage"
        template.percentage = 10.0
        template.percentage_base = "wage"

        self.Advantage.create(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
                "computation_mode": "percentage",
                "percentage": 10.0,
                "percentage_base": "wage",
            }
        )

        self.apply_contract_cron()
        payslip = self.Payslip.create({"employee_id": self.richard_emp.id})
        payslip.onchange_employee()
        contracts = payslip._get_employee_contracts()
        res = payslip.get_current_contract_dict(self.richard_contract, contracts)
        expected = self.richard_contract.wage * 10.0 / 100.0
        self.assertAlmostEqual(res.get("advantages").PCT, expected)

    def test_python_returning_non_float_raises_usererror(self):
        """A python_code formula that yields a non-numeric value must
        fail loudly (float guarantee mirrored from the payroll engine),
        not silently corrupt the payslip."""
        template = self._create_template(
            lower=0.0, upper=1000000.0, code="BAD", name="BadFormula"
        )
        template.computation_mode = "python"
        template.python_code = "result = 'not-a-number'"

        advantage = self.Advantage.new(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
            }
        )
        advantage._onchange_advantage_template_id()
        with self.assertRaises(UserError):
            advantage._compute_advantage_amount()

    def test_python_returning_int_is_coerced_to_float(self):
        """An int result is acceptable and coerced to float (no error)."""
        template = self._create_template(
            lower=0.0, upper=1000000.0, code="INTOK", name="IntOk"
        )
        template.computation_mode = "python"
        template.python_code = "result = 1500"

        advantage = self.Advantage.new(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
            }
        )
        advantage._onchange_advantage_template_id()
        amount = advantage._compute_advantage_amount()
        self.assertEqual(amount, 1500.0)
        self.assertIsInstance(amount, float)

    # ------------------------------------------------------------------
    # Quantity (enhancement: amount = quantity x unit value)
    # ------------------------------------------------------------------

    def test_quantity_defaults_keep_backward_compat(self):
        """Default quantity mode 'fixed' / value 1.0 -> amount equals
        the unit value (historical behaviour)."""
        template = self._create_template(default=200.0, upper=1000000.0)
        adv = self.Advantage.new(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
            }
        )
        adv._onchange_advantage_template_id()
        self.assertEqual(adv.quantity_mode, "fixed")
        self.assertEqual(adv.quantity_fixed_value, 1.0)
        self.assertEqual(adv._compute_advantage_amount(), 200.0)

    def test_fixed_quantity_multiplies_unit_value(self):
        template = self._create_template(
            lower=0.0, upper=1000000.0, code="QF", name="QtyFixed"
        )
        adv = self.Advantage.create(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
                "computation_mode": "fixed",
                "fixed_value": 410.0,
                "quantity_mode": "fixed",
                "quantity_fixed_value": 22.0,
            }
        )
        self.assertAlmostEqual(adv._compute_advantage_amount(), 22.0 * 410.0)

    def test_python_quantity_times_python_unit_value(self):
        """Both quantity and unit value computed by python."""
        template = self._create_template(
            lower=0.0, upper=1000000.0, code="QP", name="QtyPy"
        )
        adv = self.Advantage.create(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
                "computation_mode": "python",
                "python_code": "result = 1000.0",
                "quantity_mode": "python",
                "quantity_python_code": "result = 3",
            }
        )
        self.assertAlmostEqual(adv._compute_advantage_amount(), 3 * 1000.0)

    def test_quantity_advantage_param_accessible_in_formula(self):
        """The quantity formula can read advantage.quantity_fixed_value
        as a free parameter (pattern used by PF meal templates:
        meals_per_day stored there)."""
        template = self._create_template(
            lower=0.0, upper=1000000.0, code="QPARAM", name="QtyParam"
        )
        adv = self.Advantage.create(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
                "computation_mode": "fixed",
                "fixed_value": 410.0,
                "quantity_mode": "python",
                "quantity_fixed_value": 2.0,  # e.g. meals per day
                "quantity_python_code": "result = 10 * advantage.quantity_fixed_value",
            }
        )
        # 10 days x 2 meals/day x 410 unit value
        self.assertAlmostEqual(adv._compute_advantage_amount(), 10 * 2.0 * 410.0)
