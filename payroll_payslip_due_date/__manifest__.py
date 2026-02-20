# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Payroll Payslip Due Date",
    "version": "16.0.1.0.0",
    "sumarry": "Compute payslip due date based on workdays",
    "category": "Payroll",
    "website": "https://github.com/OCA/payroll",
    "license": "LGPL-3",
    "maintainers": ["CristianoMafraJunior"],
    "author": "Escodoo, Odoo Community Association (OCA)",
    "depends": [
        "payroll",
    ],
    "data": [
        "views/res_config_settings_views.xml",
        "views/hr_payslip_views.xml",
    ],
}
