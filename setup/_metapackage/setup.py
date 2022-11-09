import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-payroll",
    description="Meta package for oca-payroll Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-hr_payroll_period',
        'odoo14-addon-payroll',
        'odoo14-addon-payroll_account',
        'odoo14-addon-payroll_contract_advantages',
        'odoo14-addon-payroll_hr_public_holidays',
        'odoo14-addon-payroll_rule_time_parameter',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
