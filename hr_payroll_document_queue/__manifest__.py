# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "HR - Payroll Document - Queue",
    "summary": "Process a PDF payslip aynchronously.",
    "author": "PyTech, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/payroll",
    "license": "AGPL-3",
    "category": "Payrolls",
    "version": "18.0.1.0.0",
    "maintainers": [
        "SirPyTech",
    ],
    "depends": [
        "hr_payroll_document",
        "queue_job",
    ],
    "data": [
        "wizards/payroll_management_wizard_views.xml",
    ],
}
