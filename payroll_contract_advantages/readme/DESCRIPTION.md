This module adds support for advantages templates and advantages to be
set in contract form. The advantages can be set in the contract form as
a list of advantages templates. Then it can be used in the calculation
of the salary rules.

Each advantage has a computation mode (fixed value, percentage of a
contract field, or Python expression) giving a unit value, and a
quantity mode (fixed or Python). The final amount is the unit value
times the quantity, re-evaluated per payslip. The default fixed mode
and quantity 1.0 reproduce the historical behaviour. Template bounds
are enforced on the final amount.
