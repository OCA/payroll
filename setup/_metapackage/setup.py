import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-payroll",
    description="Meta package for oca-payroll Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-payroll>=16.0dev,<16.1dev',
        'odoo-addon-payroll_account>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
