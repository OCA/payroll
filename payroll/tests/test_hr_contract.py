# Part of Odoo. See LICENSE file for full copyright and licensing details.

from .common import TestPayslipBase


class TestHrContract(TestPayslipBase):
    def _schedule_pay_selection(self, lang=None):
        Contract = self.Contract.with_context(lang=lang) if lang else self.Contract
        return Contract.fields_get(["schedule_pay"])["schedule_pay"]["selection"]

    def test_schedule_pay_semi_monthly(self):
        """Twice a month is a pay frequency of its own.

        It is neither bi-weekly (every two weeks) nor bi-monthly (every two
        months).
        """
        keys = [key for key, _label in self._schedule_pay_selection()]
        self.assertIn("semi-monthly", keys)
        self.assertIn("bi-weekly", keys)
        self.assertIn("bi-monthly", keys)

        self.richard_contract.schedule_pay = "semi-monthly"
        self.assertEqual(self.richard_contract.schedule_pay, "semi-monthly")

    def test_schedule_pay_labels_are_distinct(self):
        labels = [label for _key, label in self._schedule_pay_selection()]
        self.assertEqual(len(labels), len(set(labels)))
