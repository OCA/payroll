from odoo import fields, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    line_manually_ids = fields.One2many(
        "hr.payslip.line.manually",
        "res_id",
        string="Manual Payslip Lines",
        domain=[("model", "=", "hr.payslip")],
        context={"default_model": "hr.payslip"},
        copy=True,
    )

    def _compute_payslip_line(self, rule, localdict, lines_dict):
        self.ensure_one()
        localdict["rule"] = rule
        localdict.pop("result_list", None)
        payslip_lines = rule._compute_rule(localdict)
        if not isinstance(payslip_lines, list):
            payslip_lines = [payslip_lines]
        for payslip_line in payslip_lines:
            values = payslip_line
            total = values["quantity"] * values["rate"] * values["amount"] / 100.0
            localdict = self._sum_salary_rule_category(
                localdict, rule.category_id, total
            )
            key = (
                rule.code
                + "-"
                + str(localdict["contract"].id)
                + "-"
                + str(values.get("analytic_account_id"))
            )
            lines_dict[key] = {
                "salary_rule_id": rule.id,
                "contract_id": localdict["contract"].id,
                "name": values.get("name") or rule.name,
                "code": rule.code,
                "category_id": rule.category_id.id,
                "sequence": rule.sequence,
                "appears_on_payslip": rule.appears_on_payslip,
                "parent_rule_id": rule.parent_rule_id.id,
                "condition_select": rule.condition_select,
                "condition_python": rule.condition_python,
                "condition_range": rule.condition_range,
                "condition_range_min": rule.condition_range_min,
                "condition_range_max": rule.condition_range_max,
                "amount_select": rule.amount_select,
                "amount_fix": rule.amount_fix,
                "amount_python_compute": rule.amount_python_compute,
                "amount_percentage": rule.amount_percentage,
                "amount_percentage_base": rule.amount_percentage_base,
                "register_id": rule.register_id.id,
                "employee_id": localdict["employee"].id,
                "quantity": values["quantity"],
                "rate": values["rate"],
                "amount": values["amount"],
                "analytic_account_id": values.get("analytic_account_id"),
            }
        return localdict, lines_dict
