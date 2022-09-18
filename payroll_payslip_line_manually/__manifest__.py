# Copyright 2019-2022 AppsToGROW - Henrik Norlin
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Manual payslip lines, with analytic account",
    "summary": "Easily create and use salary rules",
    "author": "AppsToGROW, Odoo Community Association (OCA)",
    "category": "Human Resources",
    "data": [
        "security/ir.model.access.csv",
        "views/hr_contract_views.xml",
        "views/hr_payslip_views.xml",
        "views/hr_salary_rule_views.xml",
    ],
    "demo": [
        "demo/hr_salary_rule_demo.xml",
    ],
    "depends": [
        "analytic",
        "payroll",
    ],
    "license": "AGPL-3",
    "maintainers": ["appstogrow"],
    "version": "14.0.1.0.0",
    "website": "https://github.com/OCA/payroll",
}
