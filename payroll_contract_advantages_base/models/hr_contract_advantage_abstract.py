# Copyright 2026 INVITU (<https://www.invitu.com>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import Command, models

# Fields copied from the template onto a new advantage. Update here
# when a new field is added to the template/advantage definition.
_TEMPLATE_FIELDS = (
    "computation_mode",
    "percentage",
    "percentage_base",
    "python_code",
    "quantity_mode",
    "quantity_fixed_value",
    "quantity_python_code",
)


class HrContractAdvantageAbstract(models.AbstractModel):
    _name = "hr.contract.advantage.abstract"
    _description = "Sync advantages from applicable templates"

    def _get_applicable_advantage_templates(self):
        """Templates that should yield an advantage on this contract.

        Returns an empty recordset by default. Bridge modules override
        this to plug a selection criterion (e.g. salary structure).
        """
        return self.env["hr.contract.advantage.template"]

    def _copy_template_fields(self, template):
        """Build the vals copied from a template onto a new advantage.

        Bridge modules and downstream addons can extend this to
        propagate extra fields they add.
        """
        vals = {name: template[name] for name in _TEMPLATE_FIELDS}
        # 'amount' (unit value) starts at the template default value;
        # non-fixed modes recompute it on the payslip anyway.
        vals["amount"] = template.default_value
        return vals

    def _sync_advantages_from_templates(self):
        """Add a hr.contract.advantage for each applicable template
        not already attached. Additive only: never removes nor
        overwrites existing lines. Works both in onchange (in-memory)
        and from code (persisted on save), by assigning Commands to
        the x2many field rather than calling create() directly.
        """
        for contract in self:
            existing = contract.advantages_ids.advantage_template_id
            templates = contract._get_applicable_advantage_templates() - existing
            if not templates:
                continue
            contract.advantages_ids = [
                Command.create(
                    {
                        **contract._copy_template_fields(template),
                        "advantage_template_id": template.id,
                    }
                )
                for template in templates
            ]
