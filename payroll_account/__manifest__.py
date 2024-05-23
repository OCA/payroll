# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Payroll Accounting",
    "version": "16.0.1.1.0",
    "category": "Payroll",
    "website": "https://github.com/OCA/payroll",
    "license": "LGPL-3",
    "summary": "Manage your payroll to accounting",
    "author": "Odoo SA, Odoo Community Association (OCA)",
    "depends": ["payroll", "account"],
    "data": [
        "views/hr_payroll_account_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "demo": ["demo/hr_payroll_account_demo.xml"],
    "maintainers": ["appstogrow", "nimarosa"],
}
