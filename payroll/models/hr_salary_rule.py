# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class HrSalaryRule(models.Model):
    _name = "hr.salary.rule"
    _order = "sequence, id"
    _description = "Salary Rule"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True,
        help="The code of salary rules can be used as reference in computation "
        "of other rules. In that case, it is case sensitive.",
    )
    sequence = fields.Integer(
        required=True, index=True, default=5, help="Use to arrange calculation sequence"
    )
    quantity = fields.Char(
        default="1.0",
        help="It is used in computation for percentage and fixed amount. "
        "For e.g. A rule for Meal Voucher having fixed amount of "
        "1€ per worked day can have its quantity defined in expression "
        "like worked_days.WORK100.number_of_days.",
    )
    category_id = fields.Many2one(
        "hr.salary.rule.category", string="Category", required=True
    )
    active = fields.Boolean(
        default=True,
        help="If the active field is set to false, it will allow you to hide"
        " the salary rule without removing it.",
    )
    appears_on_payslip = fields.Boolean(
        string="Appears on Payslip",
        default=True,
        help="Used to display the salary rule on payslip.",
    )
    parent_rule_id = fields.Many2one(
        "hr.salary.rule", string="Parent Salary Rule", index=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    condition_select = fields.Selection(
        [("none", "Always True"), ("range", "Range"), ("python", "Python Expression")],
        string="Condition Based on",
        default="none",
        required=True,
    )
    condition_range = fields.Char(
        string="Range Based on",
        default="contract.wage",
        help="This will be used to compute the % fields values; in general it "
        "is on basic, but you can also use categories code fields in "
        "lowercase as a variable names (hra, ma, lta, etc.) and the "
        "variable basic.",
    )
    condition_python = fields.Text(
        string="Python Condition",
        required=True,
        default="""
            # Available variables:
            #----------------------
            # payslip: object containing the payslips
            # payslip.rule_parameter(code): get the value for the rule parameter specified.
            #   By default it gets the code for payslip date.
            # employee: hr.employee object
            # contract: hr.contract object
            # rules: object containing the rules code (previously computed)
            # categories: object containing the computed salary rule categories
            #    (sum of amount of all rules belonging to that category).
            # worked_days: object containing the computed worked days
            # inputs: object containing the computed inputs
            # payroll: object containing miscellaneous values related to payroll
            # current_contract: object with values calculated from the current contract
            # result_rules: object with a dict of qty, rate, amount an total of calculated rules

            # Available compute variables:
            #-------------------------------
            # result: returned value have to be set in the variable 'result'

            # Example:
            #-------------------------------
            result = rules.NET > categories.NET * 0.10

            """,
        help="Applied this rule for calculation if condition is true. You can "
        "specify condition like basic > 1000.",
    )
    condition_range_min = fields.Float(
        string="Minimum Range", help="The minimum amount, applied for this rule."
    )
    condition_range_max = fields.Float(
        string="Maximum Range", help="The maximum amount, applied for this rule."
    )
    amount_select = fields.Selection(
        [
            ("percentage", "Percentage (%)"),
            ("fix", "Fixed Amount"),
            ("code", "Python Code"),
        ],
        string="Amount Type",
        index=True,
        required=True,
        default="fix",
        help="The computation method for the rule amount.",
    )
    amount_fix = fields.Float(string="Fixed Amount", digits="Payroll")
    amount_percentage = fields.Float(
        string="Percentage (%)",
        digits="Payroll Rate",
        help="For example, enter 50.0 to apply a percentage of 50%",
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

            # Available compute variables:
            #-------------------------------
            # result: returned value have to be set in the variable 'result'
            # result_rate: the rate that will be applied to "result".
            # result_qty: the quantity of units that will be multiplied to "result".
            # result_name: if this variable is computed, it will contain the name of the line.

            # Example:
            #-------------------------------
            result = contract.wage * 0.10

            """,
    )
    amount_percentage_base = fields.Char(
        string="Percentage based on", help="result will be affected to a variable"
    )
    child_ids = fields.One2many(
        "hr.salary.rule", "parent_rule_id", string="Child Salary Rule", copy=True
    )
    register_id = fields.Many2one(
        "hr.contribution.register",
        string="Contribution Register",
        help="Eventual third party involved in the salary payment of the employees.",
    )
    input_ids = fields.One2many("hr.rule.input", "input_id", string="Inputs", copy=True)
    note = fields.Text(string="Description")

    @api.constrains("parent_rule_id")
    def _check_parent_rule_id(self):
        if not self._check_recursion(parent="parent_rule_id"):
            raise ValidationError(
                _("Error! You cannot create recursive hierarchy of Salary Rules.")
            )

    def _recursive_search_of_rules(self):
        """
        @return: returns a list of tuple (id, sequence) which are all the
                 children of the passed rule_ids
        """
        children_rules = []
        for rule in self.filtered(lambda rule: rule.child_ids):
            children_rules += rule.child_ids._recursive_search_of_rules()
        return [(rule.id, rule.sequence) for rule in self] + children_rules

    # TODO should add some checks on the type of result (should be float)
    def _compute_rule(self, localdict):
        """
        :param localdict: dictionary containing the environement in which to
                          compute the rule
        :return: returns a tuple build as the base/amount computed, the quantity
                 and the rate
        :rtype: (float, float, float)
        """
        self.ensure_one()
        if self.amount_select == "fix":
            try:
                return (
                    self.amount_fix,
                    float(safe_eval(self.quantity, localdict)),
                    100.0,
                    False,  # result_name is always False if not computed by python.
                )
            except Exception:
                raise UserError(
                    _("Wrong quantity defined for salary rule %s (%s).")
                    % (self.name, self.code)
                )
        elif self.amount_select == "percentage":
            try:
                return (
                    float(safe_eval(self.amount_percentage_base, localdict)),
                    float(safe_eval(self.quantity, localdict)),
                    self.amount_percentage,
                    False,  # result_name is always False if not computed by python.
                )
            except Exception:
                raise UserError(
                    _(
                        "Wrong percentage base or quantity defined for salary "
                        "rule %s (%s)."
                    )
                    % (self.name, self.code)
                )
        else:
            try:
                safe_eval(
                    self.amount_python_compute, localdict, mode="exec", nocopy=True
                )
                result_qty = 1.0
                result_rate = 100.0
                result_name = False
                if "result_name" in localdict:
                    result_name = localdict["result_name"]
                if "result_qty" in localdict:
                    result_qty = localdict["result_qty"]
                if "result_rate" in localdict:
                    result_rate = localdict["result_rate"]
                return (
                    float(localdict["result"]),
                    float(result_qty),
                    float(result_rate),
                    result_name,
                )
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

    def _satisfy_condition(self, localdict):
        """
        @param contract_id: id of hr.contract to be tested
        @return: returns True if the given rule match the condition for the
                 given contract. Return False otherwise.
        """
        self.ensure_one()

        if self.condition_select == "none":
            return True
        elif self.condition_select == "range":
            try:
                result = safe_eval(self.condition_range, localdict)
                return (
                    self.condition_range_min <= result <= self.condition_range_max
                    or False
                )
            except Exception:
                raise UserError(
                    _("Wrong range condition defined for salary rule %s (%s).")
                    % (self.name, self.code)
                )
        else:  # python code
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
