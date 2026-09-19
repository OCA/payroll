# Copyright 2026 INVITU (<https://www.invitu.com>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.addons.payroll.tests.common import TestPayslipBase


class TestPayrollContractAdvantagesStructure(TestPayslipBase):
    def setUp(self):
        super().setUp()
        self.Template = self.env["hr.contract.advantage.template"]
        self.Advantage = self.env["hr.contract.advantage"]
        self.structure = self.developer_pay_structure
        self.template = self.Template.create(
            {
                "name": "Meal",
                "code": "MEAL",
                "default_value": 10.0,
                "upper_bound": 1000.0,
                "structure_ids": [(6, 0, [self.structure.id])],
            }
        )

    def test_hook_returns_templates_of_structure(self):
        self.richard_contract.struct_id = self.structure
        templates = self.richard_contract._get_applicable_advantage_templates()
        self.assertIn(self.template, templates)

    def test_sync_creates_missing_advantage(self):
        self.richard_contract.struct_id = self.structure
        self.richard_contract._sync_advantages_from_templates()
        advantages = self.richard_contract.advantages_ids
        self.assertEqual(len(advantages), 1)
        self.assertEqual(advantages.advantage_template_id, self.template)
        self.assertEqual(advantages.amount, 10.0)

    def test_sync_is_idempotent(self):
        self.richard_contract.struct_id = self.structure
        self.richard_contract._sync_advantages_from_templates()
        self.richard_contract._sync_advantages_from_templates()
        self.assertEqual(len(self.richard_contract.advantages_ids), 1)

    def test_sync_is_additive_only(self):
        """Pre-existing advantages are kept untouched."""
        other = self.Template.create(
            {"name": "Phone", "code": "PHONE", "default_value": 5.0}
        )
        self.Advantage.create(
            {
                "contract_id": self.richard_contract.id,
                "advantage_template_id": other.id,
                "amount": 5.0,
            }
        )
        self.richard_contract.struct_id = self.structure
        self.richard_contract._sync_advantages_from_templates()
        templates = self.richard_contract.advantages_ids.advantage_template_id
        self.assertIn(self.template, templates)
        self.assertIn(other, templates)
