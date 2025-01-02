# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class HrSalaryTableTemplate(models.Model):
    _name = "hr.salary.table.template"
    _description = "Salary Table"
    _order = "sequence"

    name = fields.Char(required=True)
    code = fields.Char()
    sequence = fields.Integer()
    type_1_id = fields.Many2one("hr.data.type")
    type_2_id = fields.Many2one("hr.data.type")
    type_3_id = fields.Many2one("hr.data.type")
    line_ids = fields.One2many(
        comodel_name="hr.salary.table",
        inverse_name="template_id",
    )
    note = fields.Text()
    active = fields.Boolean(default=True)

    def get_all_salary_table_lines(self, active_date):
        """
        Return all active salary table lines,
        that at a later step can be looked up to find specific rule values.

        Used on Payslips, to query and cache ahead of time all salary table lines,
        to be available for lookup by the rule calculations.
        """
        ids = self.ids or self.search([]).ids
        domain = [
            ("table_id.template_id", "in", ids),
            "|",
            ("table_id.date_start", "<=", active_date),
            ("table_id.date_start", "=", False),
            "|",
            ("table_id.date_end", ">=", active_date),
            ("table_id.date_end", "=", False),
        ]
        return self.env["hr.salary.table.line"].search(domain)


class HrSalaryTable(models.Model):
    _name = "hr.salary.table"
    _description = "Salary Table Period"

    template_id = fields.Many2one("hr.salary.table.template", required=True)
    company_id = fields.Many2one("res.company")
    date_start = fields.Date()
    date_end = fields.Date()
    line_ids = fields.One2many(
        comodel_name="hr.salary.table.line",
        inverse_name="table_id",
    )
    note = fields.Text()

    template_code = fields.Char(related="template_id.code")
    type_1_id = fields.Many2one("hr.data.type", related="template_id.type_1_id")
    type_2_id = fields.Many2one("hr.data.type", related="template_id.type_2_id")
    type_3_id = fields.Many2one("hr.data.type", related="template_id.type_3_id")


class HrSalaryTableLine(models.Model):
    _name = "hr.salary.table.line"
    _description = "Salary Table Values"
    _order = "table_sequence desc, value_1_id, value_2_id, value_3_id, number_from"

    table_id = fields.Many2one("hr.salary.table")
    table_sequence = fields.Integer(
        related="table_id.template_id.sequence",
        store=True,
    )

    salary_rule_id = fields.Many2one("hr.salary.rule")
    salary_rule_code = fields.Char(related="salary_rule_id.code")
    value_1_id = fields.Many2one(
        "hr.data.type.value",
        domain="[('type_id', '=', type_1_id)]",
    )
    value_2_id = fields.Many2one(
        "hr.data.type.value",
        domain="[('type_id', '=', type_2_id)]",
    )
    value_3_id = fields.Many2one(
        "hr.data.type.value",
        domain="[('type_id', '=', type_3_id)]",
    )
    number_from = fields.Float()
    number_to = fields.Float()
    result = fields.Float()

    template_id = fields.Many2one(
        "hr.salary.table.template", related="table_id.template_id", store=True
    )
    company_id = fields.Many2one(
        comodel_name="res.company", related="table_id.company_id", store=True
    )
    date_start = fields.Date(related="table_id.date_start", store=True)
    date_end = fields.Date(related="table_id.date_end", store=True)

    template_code = fields.Char(
        string="Template Code",
        related="table_id.template_id.code",
    )
    type_1_id = fields.Many2one(
        "hr.data.type", related="table_id.template_id.type_1_id"
    )
    type_2_id = fields.Many2one(
        "hr.data.type", related="table_id.template_id.type_2_id"
    )
    type_3_id = fields.Many2one(
        "hr.data.type", related="table_id.template_id.type_3_id"
    )

    @api.model
    def _get_salary_table_line_domain(self, contract, rule_code=None, amount=0):
        domain = []
        if rule_code:
            domain.append(("salary_rule_code", "=", rule_code))
        if self.type_1_id:
            value_1 = contract.get_data_value(self.type_1_id)
            domain.append(("type_1_id", "=", value_1))
        if self.type_2_id:
            value_2 = contract.get_data_value(self.type_1_id)
            domain.append(("type_2_id", "=", value_2))
        if self.type_3_id:
            value_3 = contract.get_data_value(self.type_1_id)
            domain.append(("type_3_id", "=", value_3))
        if amount:
            domain += [("number_from", "<=", amount), ("number_to", ">", amount)]
        return domain

    def lookup_rule(self, contract, rule_code, amount=0):
        """
        Given a recordset of salary table lines,
        lookup the active value for a salary rule.
        Sort order is important, as the first record is the value to be returned.

        Used by payslip rule calculations.
        """
        domain = self._get_salary_table_line_domain(contract, rule_code, amount)
        return self.filtered_domain(domain)[:1]
