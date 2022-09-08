# Copyright 2019 - Eficent http://www.eficent.com/
# Copyright 2019 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Human Resources Payslip Change State",
    "summary": "Change the state of many payslips at a time",
    "version": "14.0.1.1.0",
    "license": "AGPL-3",
    "category": "Human Resources",
    "website": "https://github.com/OCA/payroll",
    "author": "Eficent, Odoo Community Association (OCA)",
    "depends": ["hr_payroll_cancel"],
    "data": [
        "wizard/hr_payslip_change_state_view.xml",
        "security/ir.model.access.csv",
    ],
    "maintainers": ["appstogrow", "nimarosa"],
    "installable": True,
}
