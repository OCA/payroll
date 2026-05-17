This module lets you define advantage templates and set advantages on
the contract form, for use in salary rule computation.

Each advantage has a computation mode (fixed value, percentage of a
contract field, or Python expression) and a quantity mode (fixed or
Python); the amount is quantity x unit value, re-evaluated per payslip.
The default fixed mode reproduces the historical behaviour. Template
bounds are enforced on the final amount.
