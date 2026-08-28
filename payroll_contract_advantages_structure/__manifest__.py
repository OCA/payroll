# Copyright 2026 INVITU (<https://www.invitu.com>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Payroll Contract Advantages by Salary Structure",
    "version": "18.0.1.0.0",
    "category": "Payroll",
    "website": "https://github.com/OCA/payroll",
    "summary": "Attach advantage templates to salary structures and"
    " auto-create the advantages on the contract.",
    "license": "LGPL-3",
    "author": "INVITU, Odoo Community Association (OCA)",
    "depends": ["payroll_contract_advantages_base"],
    "data": [
        "views/hr_contract_advantage_template_views.xml",
        "views/hr_payroll_structure_views.xml",
    ],
    "demo": ["demo/payroll_contract_advantages_structure_demo.xml"],
    "installable": True,
}
