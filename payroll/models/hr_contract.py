# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """

    _inherit = "hr.contract"
    _description = "Employee Contract"

    struct_id = fields.Many2one("hr.payroll.structure", string="Salary Structure")
    # bi-weekly: every two weeks (26 payslips a year); semi-monthly: twice a
    # month (24 payslips a year); bi-monthly: every two months.
    schedule_pay = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi-annually", "Semi-annually"),
            ("annually", "Annually"),
            ("weekly", "Weekly"),
            ("bi-weekly", "Bi-weekly"),
            ("semi-monthly", "Semi-monthly"),
            ("bi-monthly", "Bi-monthly"),
        ],
        string="Scheduled Pay",
        index=True,
        default="monthly",
        help="Defines the frequency of the wage payment.",
    )
    resource_calendar_id = fields.Many2one(
        required=True, help="Employee's working schedule."
    )

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by
                 hierachy (parent=False first, then first level children and
                 so on) and without duplicates
        """
        # TODO: remove, too simple and not used
        return self.struct_id.get_structure_with_parents()

    @api.model
    def _get_default_payroll_structure(self, employee):
        """Default salary structure: employee, else company."""
        return employee.payroll_structure_id or self.env.company.payroll_structure_id

    @api.onchange("employee_id")
    def _onchange_employee_id_default_structure(self):
        """Set struct_id from the default when the employee changes."""
        for contract in self:
            structure = self._get_default_payroll_structure(contract.employee_id)
            if structure:
                contract.struct_id = structure.id

    @api.onchange("struct_id")
    def _onchange_struct_id_default_warning(self):
        """Warn when the chosen structure differs from the default."""
        if not self.struct_id:
            return
        structure = self._get_default_payroll_structure(self.employee_id)
        if structure and structure != self.struct_id:
            return {
                "warning": {
                    "title": _("Warning: default salary structure"),
                    "message": _(
                        "Selected structure differs from the default for "
                        "this employee/company (expected: %s).",
                        structure.display_name,
                    ),
                }
            }
