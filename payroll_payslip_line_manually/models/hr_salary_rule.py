from odoo import fields, models


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    analytic_account_id = fields.Many2one(
        "account.analytic.account", "Analytic Account"
    )
    line_manually_model = fields.Selection(
        [("hr.contract", "Contract"), ("hr.payslip", "Payslip")],
        string="Salary Rule input from",
    )

    def _reset_localdict_values(self, localdict):
        localdict["rule"] = self
        localdict.pop("result_list", None)
        return super(HrSalaryRule, self)._reset_localdict_values(localdict)

    def _compute_rule_python(self, localdict):
        if "result_list" in localdict:
            # Return list of values dictionary. Each dictionary will be a payslip line.
            result_list = []
            for result_dict in localdict["result_list"]:
                values = super(HrSalaryRule, self)._compute_rule_python(result_dict)
                values["analytic_account_id"]: result_dict.get("result_analytic")
                result_list.append(values)
            return result_list
        else:
            return super(HrSalaryRule, self)._compute_rule_python(localdict)

    def _satisfy_condition_python(self, localdict):
        localdict["rule"] = self
        return super(HrSalaryRule, self)._satisfy_condition_python(localdict)
