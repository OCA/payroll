Manage your employee payroll records.

This module is a backport from Odoo SA and as such, it is not included
in the OCA CLA. That means we do not have a copy of the copyright on it
like all other OCA modules.

## Extension hook

Localization modules can extend `_copy_refund_payslip()` to attach a reference
to retained calculation evidence before the refund is confirmed. This is useful
when the original evidence uses `copy=False` and must remain tied to the original
calculation instead of being recomputed from current employment settings.

The hook returns the draft full-refund copy. The existing refund workflow still
assigns its number, confirms it without recalculating salary lines and records
the refund reference on the original payslip.
