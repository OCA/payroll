Manage your employee payroll records.

This module is a backport from Odoo SA and as such, it is not included
in the OCA CLA. That means we do not have a copy of the copyright on it
like all other OCA modules.

## Refund defaults

Localization modules can extend `_prepare_refund_payslip()` to include a
reference to retained calculation evidence in the defaults for the refund.
The refund workflow copies the original payslip, assigns its number and
confirms it without recalculating the original salary lines.
