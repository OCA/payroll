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
        [("none", "Always True"), ("range", "Range")],
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

    def _reset_localdict_values(self, localdict):
        localdict["result_name"] = None
        localdict["result_qty"] = 1.0
        localdict["result_rate"] = 100
        localdict["result"] = None
        return localdict

    # TODO should add some checks on the type of result (should be float)
    def _compute_rule(self, localdict):
        """
        :param localdict: dictionary containing the environement in which to
                          compute the rule
        :return: returns a dict with values for the payslip line.
                 The dict should minimum have "name", "quantity", "rate" and "amount".
        :rtype: {"name": string, "quantity": float, "rate": float, "amount": float}
        """
        self.ensure_one()
        method = "_compute_rule_{}".format(self.amount_select)
        return api.call_kw(self, method, [self.ids, localdict], {})

    def _compute_rule_fix(self, localdict):
        try:
            return {
                "name": self.name,
                "quantity": float(safe_eval(self.quantity, localdict)),
                "rate": 100.0,
                "amount": self.amount_fix,
            }
        except Exception:
            raise UserError(
                _("Wrong quantity defined for salary rule %s (%s).")
                % (self.name, self.code)
            )

    def _compute_rule_percentage(self, localdict):
        try:
            return {
                "name": self.name,
                "quantity": float(safe_eval(self.quantity, localdict)),
                "rate": self.amount_percentage,
                "amount": float(safe_eval(self.amount_percentage_base, localdict)),
            }
        except Exception:
            raise UserError(
                _(
                    "Wrong percentage base or quantity defined for salary "
                    "rule %s (%s)."
                )
                % (self.name, self.code)
            )

    def _get_rule_dict(self, localdict):
        name = localdict.get("result_name") or self.name
        quantity = float(localdict["result_qty"]) if "result_qty" in localdict else 1.0
        rate = float(localdict["result_rate"]) if "result_rate" in localdict else 100.0
        return {
            "name": name,
            "quantity": quantity,
            "rate": rate,
            "amount": float(localdict["result"]),
        }

    def _satisfy_condition(self, localdict):
        """
        @param contract_id: id of hr.contract to be tested
        @return: returns True if the given rule match the condition for the
                 given contract. Return False otherwise.
        """
        self.ensure_one()
        method = "_satisfy_condition_{}".format(self.condition_select)
        return api.call_kw(self, method, [self.ids, localdict], {})

    def _satisfy_condition_none(self, localdict):
        return True

    def _satisfy_condition_range(self, localdict):
        try:
            result = safe_eval(self.condition_range, localdict)
            return (
                self.condition_range_min <= result <= self.condition_range_max or False
            )
        except Exception:
            raise UserError(
                _("Wrong range condition defined for salary rule %s (%s).")
                % (self.name, self.code)
            )
