`payroll` derives a payslip's worked days from the resource calendar: what the
employee **should** have worked.

Where an installation records `hr.work.entry` — attendances, overtime, absences —
that data describes what actually **was** worked. This module makes the payslip
use it.

Without this, a payroll for a workforce that clocks in silently ignores its own
attendance records: overtime is never paid, and absences never deducted, because
the calendar says every day was a full one.
