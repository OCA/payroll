# Copyright 2026 Anderson Oliveira
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import date

from psycopg2.errors import UniqueViolation

from odoo.exceptions import UserError
from odoo.tests import common
from odoo.tools import mute_logger

# Fixtures are built here on purpose: the OCA CI runs without demo data.


class TestRuleParameter(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.parameter = cls.env["hr.rule.parameter"].create(
            {"name": "Test Rate", "code": "test_rate"}
        )
        cls.value_2025 = cls.env["hr.rule.parameter.value"].create(
            {
                "rule_parameter_id": cls.parameter.id,
                "date_from": date(2025, 1, 1),
                "parameter_value": "0.10",
            }
        )
        cls.value_2026 = cls.env["hr.rule.parameter.value"].create(
            {
                "rule_parameter_id": cls.parameter.id,
                "date_from": date(2026, 1, 1),
                "parameter_value": "0.15",
            }
        )
        cls.RuleParameter = cls.env["hr.rule.parameter"]

    def test_value_in_force_by_date(self):
        """The value returned is the one in force on the requested date."""
        self.assertEqual(
            self.RuleParameter._get_parameter_from_code("test_rate", date(2025, 6, 15)),
            0.10,
        )
        self.assertEqual(
            self.RuleParameter._get_parameter_from_code("test_rate", date(2026, 6, 15)),
            0.15,
        )

    def test_boundary_date_is_inclusive(self):
        """A value applies from its own date_from onwards."""
        self.assertEqual(
            self.RuleParameter._get_parameter_from_code("test_rate", date(2026, 1, 1)),
            0.15,
        )
        self.assertEqual(
            self.RuleParameter._get_parameter_from_code(
                "test_rate", date(2025, 12, 31)
            ),
            0.10,
        )

    def test_structured_value(self):
        """A value may be a structure, not just a number."""
        brackets = self.env["hr.rule.parameter"].create(
            {"name": "Tax Brackets", "code": "test_brackets"}
        )
        self.env["hr.rule.parameter.value"].create(
            {
                "rule_parameter_id": brackets.id,
                "date_from": date(2026, 1, 1),
                "parameter_value": "[(0.0, 0.0, 0.0192), (7735.0, 148.51, 0.064)]",
            }
        )
        result = self.RuleParameter._get_parameter_from_code(
            "test_brackets", date(2026, 3, 1)
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1], (7735.0, 148.51, 0.064))

    def test_no_value_in_force_yet(self):
        """Asking before the first value is an error, not a silent zero."""
        with self.assertRaises(UserError):
            self.RuleParameter._get_parameter_from_code("test_rate", date(2024, 1, 1))

    def test_unknown_code(self):
        with self.assertRaises(UserError):
            self.RuleParameter._get_parameter_from_code("nope", date(2026, 1, 1))

    def test_not_raising_returns_false(self):
        self.assertFalse(
            self.RuleParameter._get_parameter_from_code(
                "nope", date(2026, 1, 1), raise_if_not_found=False
            )
        )

    @mute_logger("odoo.sql_db")
    def test_duplicate_code_is_rejected(self):
        with self.assertRaises(UniqueViolation):
            with self.env.cr.savepoint():
                self.env["hr.rule.parameter"].create(
                    {"name": "Duplicate", "code": "test_rate"}
                )

    def test_unevaluable_value_reports_the_code(self):
        broken = self.env["hr.rule.parameter"].create(
            {"name": "Broken", "code": "test_broken"}
        )
        self.env["hr.rule.parameter.value"].create(
            {
                "rule_parameter_id": broken.id,
                "date_from": date(2026, 1, 1),
                "parameter_value": "this is not python",
            }
        )
        with self.assertRaises(UserError) as caught:
            self.RuleParameter._get_parameter_from_code("test_broken", date(2026, 2, 1))
        self.assertIn("test_broken", str(caught.exception))


class TestRuleParameterInPayslip(common.TransactionCase):
    """The parameter must reach the salary rules, at the payslip's own date."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.parameter = cls.env["hr.rule.parameter"].create(
            {"name": "Contribution Rate", "code": "test_contribution"}
        )
        for year, rate in ((2025, "0.10"), (2026, "0.20")):
            cls.env["hr.rule.parameter.value"].create(
                {
                    "rule_parameter_id": cls.parameter.id,
                    "date_from": date(year, 1, 1),
                    "parameter_value": rate,
                }
            )

        cls.category = cls.env["hr.salary.rule.category"].create(
            {"name": "Basic", "code": "BASIC"}
        )
        cls.rule = cls.env["hr.salary.rule"].create(
            {
                "name": "Contribution",
                "code": "CONTRIB",
                "sequence": 10,
                "category_id": cls.category.id,
                "condition_select": "none",
                "amount_select": "code",
                "amount_python_compute": (
                    'rate = payslip.rule_parameter("test_contribution")\n'
                    "result = contract.wage * rate"
                ),
            }
        )
        cls.structure = cls.env["hr.payroll.structure"].create(
            {
                "name": "Test Structure",
                "code": "TEST",
                "rule_ids": [(4, cls.rule.id)],
            }
        )

        cls.employee = cls.env["hr.employee"].create({"name": "Test Employee"})
        cls.employee.version_id.write(
            {
                "contract_date_start": date(2025, 1, 1),
                "name": "Test Contract",
                "wage": 1000.0,
                "struct_id": cls.structure.id,
            }
        )

    def _payslip_for(self, date_from, date_to):
        payslip = self.env["hr.payslip"].create(
            {
                "employee_id": self.employee.id,
                "contract_id": self.employee.version_id.id,
                "struct_id": self.structure.id,
                "date_from": date_from,
                "date_to": date_to,
                "name": "Test payslip",
            }
        )
        payslip.compute_sheet()
        return payslip

    def test_rule_uses_rate_of_the_payslip_period(self):
        """Recomputing an old payslip must use the old rate, not today's."""
        payslip_2025 = self._payslip_for(date(2025, 6, 1), date(2025, 6, 30))
        line_2025 = payslip_2025.line_ids.filtered(lambda line: line.code == "CONTRIB")
        self.assertEqual(line_2025.total, 100.0, "1000 * 0.10 in force during 2025")

        payslip_2026 = self._payslip_for(date(2026, 6, 1), date(2026, 6, 30))
        line_2026 = payslip_2026.line_ids.filtered(lambda line: line.code == "CONTRIB")
        self.assertEqual(line_2026.total, 200.0, "1000 * 0.20 in force during 2026")
