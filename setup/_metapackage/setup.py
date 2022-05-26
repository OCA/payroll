import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-payroll",
    description="Meta package for oca-payroll Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-hr_payroll_cancel',
        'odoo14-addon-payroll',
        'odoo14-addon-payroll_account',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
