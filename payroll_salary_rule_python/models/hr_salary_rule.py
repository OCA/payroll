# Copyright (C) 2022 Henrik Norlin (<henrik@appstogrow.co>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    condition_select = fields.Selection(
        selection_add=[("python", "Python Expression")],
        ondelete={"python": "set default"},
    )
    condition_python = fields.Text(
        string="Python Condition",
        required=True,
        default="""
            # Available variables:
            #-------------------------------
            # payslip: object containing the payslips
            # employee: hr.employee object
            # contract: hr.contract object
            # rules: object containing the rules code (previously computed)
            # categories: object containing the computed salary rule categories
            #    (sum of amount of all rules belonging to that category).
            # worked_days: object containing the computed worked days.
            # inputs: object containing the computed inputs.
            # payroll: object containing miscellaneous values related to payroll
            # current_contract: object with values calculated from the current contract
            # result_rules: object with a dict of qty, rate, amount an total of calculated rules
            # tools: object that contain libraries and tools that can be used in calculations

            # Available compute variables:
            #-------------------------------
            # result: returned value have to be set in the variable 'result'

            # Example:
            #-------------------------------
            # result = worked_days.WORK0 and worked_days.WORK0.number_of_days > 0

            """,
        help="Applied this rule for calculation if condition is true. You can "
        "specify condition like basic > 1000.",
    )
    amount_select = fields.Selection(
        selection_add=[("code", "Python Code")],
        ondelete={"code": "set default"},
    )
    amount_python_compute = fields.Text(
        string="Python Code",
        default="""
            # Available variables:
            #-------------------------------
            # payslip: object containing the payslips
            # employee: hr.employee object
            # contract: hr.contract object
            # rules: object containing the rules code (previously computed)
            # categories: object containing the computed salary rule categories
            #    (sum of amount of all rules belonging to that category).
            # worked_days: object containing the computed worked days.
            # inputs: object containing the computed inputs.
            # payroll: object containing miscellaneous values related to payroll
            # current_contract: object with values calculated from the current contract
            # result_rules: object with a dict of qty, rate, amount an total of calculated rules
            # tools: object that contain libraries and tools that can be used in calculations

            # Available compute variables:
            #-------------------------------
            # result: returned value have to be set in the variable 'result'
            # result_rate: the rate that will be applied to "result".
            # result_qty: the quantity of units that will be multiplied to "result".
            # result_name: if this variable is computed, it will contain the name of the line.

            # Example:
            #-------------------------------
            # result = contract.wage * 0.10

            """,
    )

    def _satisfy_condition_python(self, localdict):
        try:
            safe_eval(self.condition_python, localdict, mode="exec", nocopy=True)
            return "result" in localdict and localdict["result"] or False
        except Exception as ex:
            raise UserError(
                _(
                    """
Wrong python condition defined for salary rule %s (%s).
Here is the error received:

%s
"""
                )
                % (self.name, self.code, repr(ex))
            )

    def _compute_rule_code(self, localdict):
        try:
            safe_eval(self.amount_python_compute, localdict, mode="exec", nocopy=True)
            return self._get_rule_dict(localdict)
        except Exception as ex:
            raise UserError(
                _(
                    """
Wrong python code defined for salary rule %s (%s).
Here is the error received:

%s
"""
                )
                % (self.name, self.code, repr(ex))
            )

    def _get_rule_dict(self, localdict):
        rule_dict = super(HrSalaryRule, self)._get_rule_dict(localdict)
        rule_dict["condition_python"] = self.condition_python
        rule_dict["amount_python_compute"] = self.amount_python_compute
        return rule_dict
