Tax brackets, contribution rates and legal thresholds are **data, not code**.

Without somewhere to put them, they end up hard-coded inside
`amount_python_compute`, and every legal update means editing every rule that
happens to use them. Recomputing an old payslip then silently applies today's
rates to a period they never applied to.

This module adds salary rule parameters whose value is **versioned by the date
it comes into force**. A legal change is a new value with a new date; the old
value stays, so historical payslips keep recomputing correctly.
