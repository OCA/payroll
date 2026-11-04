Manage your employee payroll records.

This module is a backport from Odoo SA and as such, it is not included
in the OCA CLA. That means we do not have a copy of the copyright on it
like all other OCA modules.

Models live in the ``payroll.*`` namespace (``payroll.payslip``,
``payroll.salary.rule``, ...), deliberately separate from the Enterprise
``hr_payroll`` model names (``hr.payslip``, ``hr.salary.rule``, ...).
This allows both payroll engines to be installed on the same database —
for example, different companies using different engines — without the
two modules merging into a single conflicting schema.
