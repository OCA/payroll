# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payroll',
    'category': 'Human Resources',
    'sequence': 38,
    'summary': 'Manage your employee payroll records',
    'version': '13.0.1.0.0',
    'author': "Odoo Community Association (OCA), Odoo SA",
    'license': 'LGPL-3',
    'website': 'https://github.com/OCA/payroll',
    'depends': [
        'hr_contract',
        'hr_holidays',
    ],
    'data': [
        'security/payroll_security.xml',
        'security/ir.model.access.csv',
        'wizard/payroll_payslips_by_employees_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_salary_rule_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_employee_views.xml',
        'data/payroll_sequence.xml',
        'views/payroll_report.xml',
        'data/payroll_data.xml',
        'wizard/payroll_contribution_register_report_views.xml',
        'views/res_config_settings_views.xml',
        'views/report_contributionregister_templates.xml',
        'views/report_payslip_templates.xml',
        'views/report_payslipdetails_templates.xml',
    ],
    'demo': ['data/payroll_demo.xml'],
}
