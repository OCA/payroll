# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Payroll Rule Tag",
    "version": "18.0.1.0.0",
    "category": "Payroll",
    "website": "https://github.com/OCA/payroll",
    "license": "LGPL-3",
    "author": "Daniel Reis, Odoo Community Association (OCA)",
    "depends": ["payroll"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_salary_rule.xml",
        "views/hr_salary_rule_tag.xml",
    ],
    "maintainers": ["dreispt"],
}
