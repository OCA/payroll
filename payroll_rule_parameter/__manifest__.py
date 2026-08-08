# Copyright 2026 Anderson Oliveira
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
{
    "name": "Payroll Rule Parameters",
    "version": "19.0.1.0.0",
    "category": "Payroll",
    "website": "https://github.com/OCA/payroll",
    "license": "LGPL-3",
    "summary": "Date-versioned parameters for salary rules",
    "author": "Odoo Community Association (OCA)",
    "depends": ["payroll"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_rule_parameter_views.xml",
    ],
    "installable": True,
}
