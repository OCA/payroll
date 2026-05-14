# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """

    _inherit = "hr.contract"
    _description = "Employee Contract"

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
    resource_calendar_id = fields.Many2one(
        required=True, help="Employee's working schedule."
    )

    seniority_date = fields.Date(
        help="Starting date used for seniority computation.",
    )

    opening_date = fields.Date(
        help="Cut-off date of the opening balances, not necessarily the "
        "contract start; payslips dated after it take over from these values.",
    )
    opening_leave_base = fields.Monetary(
        string="Opening Paid Leave Base",
        currency_field="currency_id",
        help="Cumulative paid leave reference base at the opening date.",
    )
    opening_leave_days = fields.Float(
        string="Opening Paid Leave Days Balance",
        digits=(16, 2),
        help="Paid leave days acquired and not yet taken at the opening date.",
    )

    payslip_ids = fields.One2many(
        "hr.payslip",
        "contract_id",
        string="Payslips",
        help="Payslips generated for this contract.",
    )
    payslip_count = fields.Integer(
        compute="_compute_payslip_count",
        help="Number of payslips on the contract; locks the opening fields.",
    )

    @api.depends("payslip_ids")
    def _compute_payslip_count(self):
        for contract in self:
            contract.payslip_count = len(contract.payslip_ids)

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by
                 hierachy (parent=False first, then first level children and
                 so on) and without duplicates
        """
        # TODO: remove, too simple and not used
        return self.struct_id.get_structure_with_parents()
