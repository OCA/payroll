# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Employee Master Data History",
    "summary": "Configure master data attributes and track their changes history.",
    "version": "18.0.1.0.0",
    "category": "Payroll",
    "website": "https://github.com/OCA/payroll",
    "license": "LGPL-3",
    "author": "Daniel Reis, Odoo Community Association (OCA)",
    "depends": ["hr_contract"],
    "data": [
        "security/hr_payroll_security.xml",
        "security/ir.model.access.csv",
        "data/hr_master_data.xml",
        "views/hr_data_value_views.xml",
        "views/hr_contract_value_views.xml",
        "views/hr_contract_views.xml",
    ],
    "demo": ["data/demo_data.xml"],
    "installable": True,
    "maintainers": ["dreispt"],
}
