# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests.common import mute_logger

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
        template = self._create_template(default=95.45)
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

    def test_constraint_allows_amount_when_bounds_unset(self):
        """A template left with default (0.0) bounds must not block every
        non-zero amount: 0.0 means "no limit on that side"."""
        template = self._create_template(lower=0.0, upper=0.0, default=0.0)

        advantage = self.Advantage.create(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
                "amount": 30.0,
            }
        )

        self.assertEqual(advantage.amount, 30.0)

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

    def test_duplicate_advantage_on_same_contract_is_rejected(self):
        """The same advantage template can't be set twice on one contract:
        it would silently overwrite one amount with the other in
        get_current_contract_dict()."""
        template = self._create_template()
        self.Advantage.create(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": template.id,
                "amount": 10.0,
            }
        )

        with (
            self.assertRaises(IntegrityError),
            mute_logger("odoo.sql_db"),
            self.cr.savepoint(),
        ):
            self.Advantage.create(
                {
                    "contract_id": self.richard_contract.id,
                    "advantage_template_id": template.id,
                    "amount": 20.0,
                }
            )

    def test_template_code_must_be_unique(self):
        """Two templates can't share the same code: it's used as the key to
        expose the advantage to salary rules (advantages.<CODE>)."""
        self._create_template(code="DUP")

        with (
            self.assertRaises(IntegrityError),
            mute_logger("odoo.sql_db"),
            self.cr.savepoint(),
        ):
            self._create_template(code="DUP", name="Other Benefit")

    def test_template_lower_bound_cannot_exceed_upper_bound(self):
        """A template can't be saved with lower_bound > upper_bound."""
        with self.assertRaises(ValidationError):
            self._create_template(lower=100.0, upper=10.0)

    def test_template_default_value_must_respect_bounds(self):
        """A template's default_value can't fall outside its own bounds."""
        with self.assertRaises(ValidationError):
            self._create_template(lower=0.0, upper=100.0, default=150.0)

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
