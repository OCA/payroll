# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Payroll Value Table",
    "version": "18.0.1.0.0",
    "category": "Payroll",
    "website": "https://github.com/OCA/payroll",
    "license": "LGPL-3",
    "author": "Daniel Reis, Odoo Community Association (OCA)",
    "depends": ["payroll", "hr_master_data"],
    "data": [
        "security/hr_payroll_security.xml",
        "security/ir.model.access.csv",
        "views/hr_salary_table_template.xml",
        "views/hr_salary_table.xml",
        "views/menu.xml",
    ],
    "maintainers": ["dreispt"],
}
