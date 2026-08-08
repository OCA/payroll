Nothing to configure. Once installed, worked-day lines are built from the
validated work entries falling inside the payslip period, grouped by the
**payroll code** of their work entry type.

Salary rules address them by that code:

    overtime = worked_days.OVERTIME
    result = (overtime.number_of_hours if overtime else 0.0) * hourly_rate

Hours come from the work entries themselves. Days are derived using the
contract calendar's `hours_per_day`, so a 12-hour shift counts as one day
rather than one and a half.

Contracts with no work entry in the period keep `payroll`'s calendar-based
computation, so installing this module changes nothing for them.

A work entry type without a payroll code is skipped: a rule has no way to
address it.

## Work entry states

Only entries in state **validated** are taken into account. Draft, cancelled
and conflicting entries are deliberately excluded: a conflict is Odoo telling
you the record is not trustworthy, and paying it would hide the problem rather
than surface it.

Note that Odoo validates **one work entry per employee and day**: a second
entry on a date that already has a validated one stays in conflict. Overtime
recorded on the same day as an attendance therefore needs a work entry model
that accounts for it, or it will never reach the payslip.
