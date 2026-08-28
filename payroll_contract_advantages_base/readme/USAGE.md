This module is a technical base; install a bridge module (e.g.
``payroll_contract_advantages_structure``) to enable the
synchronization with a real criterion.

For module developers, a bridge module needs to:

1. attach the templates to its criterion (typically a Many2many);
2. override ``_get_applicable_advantage_templates`` on ``hr.contract``
   to return the templates resolved from that criterion;
3. call ``_sync_advantages_from_templates()`` from the trigger that
   makes sense for the criterion (onchange, button, write override).

Example: bridge module ``payroll_contract_advantages_structure``
(criterion = salary structure):

```python
from odoo import api, fields, models


class HrContractAdvantageTemplate(models.Model):
    _inherit = "hr.contract.advantage.template"

    structure_ids = fields.Many2many(
        comodel_name="hr.payroll.structure",
        relation="hr_contract_advantage_template_structure_rel",
        column1="template_id",
        column2="structure_id",
        string="Salary Structures",
    )


class HrPayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"

    advantage_template_ids = fields.Many2many(
        comodel_name="hr.contract.advantage.template",
        relation="hr_contract_advantage_template_structure_rel",
        column1="structure_id",
        column2="template_id",
        string="Advantage Templates",
    )


class HrContract(models.Model):
    _inherit = "hr.contract"

    def _get_applicable_advantage_templates(self):
        return self.struct_id.advantage_template_ids

    @api.onchange("struct_id")
    def _onchange_struct_id_sync_advantages(self):
        for contract in self:
            contract._sync_advantages_from_templates()
```

The same pattern applies to any other criterion (employee tags,
department, job position...): the bridge module declares the link,
overrides the hook and picks the right trigger.
