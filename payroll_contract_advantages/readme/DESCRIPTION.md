This module adds support for advantages templates and advantages to be
set in contract form. The advantages can be set in the contract form as
a list of advantages templates. Then it can be used in the calculation
of the salary rules.

Each advantage has a computation mode (fixed value, percentage of a
contract field, or Python expression); the amount is re-evaluated per
payslip. The default fixed mode reproduces the historical behaviour.
Template bounds are enforced on the amount.
