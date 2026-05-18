- Set the advantages templates in the payroll module with lower and
  upper bounds and default value.
- Go to the employee contract and add the advantages that you want for
  this contract, default value will be populated but you can change it.
- Then in the salary rules, access this value using
  current_contract.advantages.\[ADVANTAGE_CODE\] (without brackets)
- On the template, choose a computation mode (fixed value, percentage
  of a contract field, or Python code) and a quantity mode (fixed or
  Python code). The definition is copied onto the advantage and can be
  tuned per contract.
- ``amount`` holds the unit value; the final amount is the unit value
  times the quantity, re-evaluated for each payslip. Python formulas
  expose ``advantage``, ``contract``, ``employee``, ``payslip`` and
  must set ``result``.
- Bounds are enforced on the final amount; a non-numeric formula
  result raises an error.
