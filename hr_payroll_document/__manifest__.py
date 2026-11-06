{
    "name": "HR - Payroll Document",
    "summary": "Manage payroll for each employee",
    "author": "APSL, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/payroll",
    "development_status": "Production/Stable",
    "license": "AGPL-3",
    "category": "Payrolls",
    "version": "16.0.1.3.2",
    "depends": ["hr", "base_vat"],
    "maintainers": ["peluko00"],
    "external_dependencies": {
        "python": [
            "pypdf<7",
        ],
    },
    "data": [
        "wizard/payroll_management_wizard.xml",
        "security/ir.model.access.csv",
        "data/email_payroll_employee.xml",
        "views/hr_employee_views.xml",
        "views/res_users_views.xml",
    ],
}
