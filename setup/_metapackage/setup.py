import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-payroll",
    description="Meta package for oca-payroll Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-payroll',
        'odoo13-addon-payroll_account',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
