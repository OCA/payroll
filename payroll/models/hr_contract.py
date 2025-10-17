# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """

    _inherit = "hr.version"
    _description = "Employee Contract / Version"

    struct_id = fields.Many2one("hr.payroll.structure", string="Salary Structure")
    schedule_pay = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi-annually", "Semi-annually"),
            ("annually", "Annually"),
            ("weekly", "Weekly"),
            ("bi-weekly", "Bi-weekly"),
            ("bi-monthly", "Bi-monthly"),
        ],
        string="Scheduled Pay",
        index=True,
        default="monthly",
        help="Defines the frequency of the wage payment.",
    )
    resource_calendar_id = fields.Many2one(help="Employee's working schedule.")

    @api.model
    def _get_whitelist_fields_from_template(self):
        whitelist = super()._get_whitelist_fields_from_template()
        for field_name in ("schedule_pay", "struct_id"):
            if field_name not in whitelist:
                whitelist.append(field_name)
        return whitelist

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by
                 hierachy (parent=False first, then first level children and
                 so on) and without duplicates
        """
        # TODO: remove, too simple and not used
        return self.struct_id.get_structure_with_parents()
