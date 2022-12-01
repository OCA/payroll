{
    "name": "Payroll Rule Time Parameter",
    "summary": "",
    "author": "nimarosa, appstogrow, Odoo Community Association (OCA)",
    "category": "Payroll",
    "data": [
        "security/ir.model.access.csv",
        "views/base_time_parameter_views.xml",
    ],
    "depends": [
        "base_time_parameter",
        "payroll",
    ],
    "external_dependencies": {
        "python": ["openupgradelib"],
    },
    "license": "LGPL-3",
    "maintainers": ["appstogrow", "nimarosa"],
    "pre_init_hook": "pre_init_hook",
    "version": "14.0.2.0.2",
    "website": "https://github.com/OCA/payroll",
}
