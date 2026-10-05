# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo.addons.payroll.models.hr_payslip import (
    BaseBrowsableObject,
    BrowsableObject,
    Payslips,
)

from .common import TestPayslipBase


class TestBrowsableObject(TestPayslipBase):
    def setUp(self):
        super().setUp()

    def test_init(self):
        obj = BrowsableObject(self.richard_emp.id, {"test": 1}, self.env)

        self.assertEqual(obj.test, 1, "Simple initialization")
        self.assertEqual(
            obj.employee_id,
            self.richard_emp.id,
            "Employee Id is retrieved successfully",
        )
        self.assertEqual(obj.env, self.env, "Env is retrieved successfully")

        d = {
            "level1": BaseBrowsableObject(
                {
                    "level2": 10,
                    "env": 900.0,
                },
            )
        }
        obj = BrowsableObject(self.richard_emp.id, d, self.env)

        self.assertEqual(obj.level1.level2, 10, "Nested initialization")
        self.assertEqual(
            obj.employee_id,
            self.richard_emp.id,
            "Employee Id is retrieved successfully from nested dictionary",
        )
        self.assertEqual(
            obj.env, self.env, "Env is retrieved successfully from nested dictionary"
        )
        self.assertEqual(
            obj.level1.employee_id, 0.0, "Employee Id is *NOT* in BaseBrowsableObject"
        )
        self.assertEqual(
            obj.level1.env,
            900.0,
            "Env is *IN* BaseBrowsableObject, but it's in user-defined dictionary",
        )

    def test_update_attribute(self):
        obj = BrowsableObject(
            self.richard_emp.id,
            {
                "foo": BaseBrowsableObject(
                    {
                        "bar": 200.0,
                    }
                )
            },
            self.env,
        )
        self.assertEqual(obj.foo.bar, 200.0, "Nested initialization succeeded")

        obj.foo.bar = 350.0
        self.assertEqual(
            obj.foo.bar,
            350.0,
            "Updating of attribute using dot ('.') notation succeeded",
        )

    def _confirmed_payslip(self, date_from, date_to, wage=None, employee=None):
        """A confirmed payslip of Richard, its BASIC line being ``wage``."""
        if wage is not None:
            self.richard_contract.wage = wage
        payslip = self.Payslip.create(
            {
                "employee_id": (employee or self.richard_emp).id,
                "contract_id": self.richard_contract.id,
                "struct_id": self.developer_pay_structure.id,
                "date_from": date_from,
                "date_to": date_to,
            }
        )
        payslip.action_payslip_done()
        return payslip

    def _max_monthly(self, from_date="2024-01-01", to_date="2024-06-30"):
        payslips = Payslips(self.richard_emp.id, self.Payslip, self.env)
        return payslips.max_monthly("BASIC", from_date, to_date)

    def test_max_monthly_without_payslips(self):
        self.assertEqual(self._max_monthly(), 0.0)

    def test_max_monthly_single_month(self):
        self._confirmed_payslip("2024-01-01", "2024-01-31", wage=5000.0)

        self.assertEqual(self._max_monthly(), 5000.0)

    def test_max_monthly_best_month_wins(self):
        self._confirmed_payslip("2024-01-01", "2024-01-31", wage=5000.0)
        self._confirmed_payslip("2024-02-01", "2024-02-29", wage=7000.0)
        self._confirmed_payslip("2024-03-01", "2024-03-31", wage=6000.0)

        self.assertEqual(self._max_monthly(), 7000.0)

    def test_max_monthly_adds_up_payslips_of_one_month(self):
        """Two payslips a month make up one monthly remuneration."""
        self._confirmed_payslip("2024-01-01", "2024-01-31", wage=5000.0)
        self._confirmed_payslip("2024-02-01", "2024-02-15", wage=3000.0)
        self._confirmed_payslip("2024-02-16", "2024-02-29", wage=3500.0)

        self.assertEqual(self._max_monthly(), 6500.0)

    def test_max_monthly_month_is_the_one_the_period_starts_in(self):
        """A payslip spanning two months counts, whole, in the first one."""
        self._confirmed_payslip("2024-01-01", "2024-01-31", wage=5000.0)
        self._confirmed_payslip("2024-01-16", "2024-02-15", wage=1500.0)
        self._confirmed_payslip("2024-02-16", "2024-02-29", wage=4000.0)

        self.assertEqual(self._max_monthly(), 6500.0)

    def test_max_monthly_subtracts_credit_notes(self):
        self._confirmed_payslip("2024-01-01", "2024-01-31", wage=5000.0)
        payslip = self._confirmed_payslip("2024-02-01", "2024-02-29", wage=7000.0)
        self.assertEqual(self._max_monthly(), 7000.0)

        payslip.refund_sheet()

        self.assertEqual(self._max_monthly(), 5000.0)

    def test_max_monthly_ignores_unconfirmed_payslips(self):
        self._confirmed_payslip("2024-01-01", "2024-01-31", wage=5000.0)
        self.richard_contract.wage = 9000.0
        draft = self.Payslip.create(
            {
                "employee_id": self.richard_emp.id,
                "contract_id": self.richard_contract.id,
                "struct_id": self.developer_pay_structure.id,
                "date_from": "2024-02-01",
                "date_to": "2024-02-29",
            }
        )
        draft.compute_sheet()

        self.assertEqual(self._max_monthly(), 5000.0)

    def test_max_monthly_only_payslips_within_the_dates(self):
        """Same rule as ``sum()``: the whole period lies between the dates."""
        self._confirmed_payslip("2023-12-01", "2023-12-31", wage=9000.0)
        self._confirmed_payslip("2024-01-01", "2024-01-31", wage=5000.0)
        self._confirmed_payslip("2024-06-16", "2024-07-15", wage=8000.0)

        self.assertEqual(self._max_monthly(), 5000.0)

    def test_max_monthly_other_employees_do_not_count(self):
        self._confirmed_payslip("2024-01-01", "2024-01-31", wage=5000.0)
        self._confirmed_payslip(
            "2024-02-01", "2024-02-29", wage=9000.0, employee=self.sally
        )

        self.assertEqual(self._max_monthly(), 5000.0)

    def test_max_monthly_in_a_salary_rule(self):
        self._confirmed_payslip("2024-01-01", "2024-01-31", wage=5000.0)
        self._confirmed_payslip("2024-02-01", "2024-02-29", wage=7000.0)
        rule = self.SalaryRule.create(
            {
                "name": "Half of the best month",
                "code": "BEST",
                "sequence": 2,
                "category_id": self.categ_alw.id,
                "condition_select": "none",
                "amount_select": "code",
                "amount_python_compute": "result = payslips.max_monthly("
                "'BASIC', '2024-01-01', payslip.date_to) / 2",
            }
        )
        self.developer_pay_structure.rule_ids = [(4, rule.id)]
        payslip = self.Payslip.create(
            {
                "employee_id": self.richard_emp.id,
                "contract_id": self.richard_contract.id,
                "struct_id": self.developer_pay_structure.id,
                "date_from": "2024-06-01",
                "date_to": "2024-06-30",
            }
        )
        payslip.compute_sheet()

        line = payslip.line_ids.filtered(lambda line: line.code == "BEST")
        self.assertEqual(line.total, 3500.0)
