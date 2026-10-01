# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Payroll Rule Tag",
    "version": "18.0.1.0.0",
    "category": "Payroll",
    "website": "https://github.com/OCA/payroll",
    "license": "LGPL-3",
    "author": "Daniel Reis, Nimarosa, Odoo Community Association (OCA)",
    "depends": ["payroll"],
    "data": [
        "security/hr_payroll_security.xml",
        "security/ir.model.access.csv",
        "views/hr_salary_rule_tag.xml",
        "views/hr_salary_rule.xml",
    ],
    "maintainers": ["dreispt", "nimarosa"],
}
