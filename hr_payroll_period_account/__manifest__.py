# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "HR Payroll Period Account",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "category": "Payroll",
    "summary": "Payroll period and accounting integration",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/payroll",
    "depends": [
        "hr_payroll_period",
        "payroll_account",
    ],
    "data": [
        "views/hr_payslip_view.xml",
    ],
    "installable": True,
}
