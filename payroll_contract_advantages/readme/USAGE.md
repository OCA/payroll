- Create advantage templates with lower/upper bounds, a computation
  mode (fixed value, percentage of a contract field, or Python code)
  and a quantity mode (fixed or Python code).
- Add advantages on the employee contract. The definition is copied
  from the template and can be tuned per contract.
- The amount is **quantity x unit value**, re-evaluated for each
  payslip. Python formulas expose ``advantage``, ``contract``,
  ``employee``, ``payslip`` and must set ``result``. The ``Quantity``
  field is also a free parameter readable via
  ``advantage.quantity_fixed_value``.
- Bounds are enforced on the final amount; a non-numeric formula result
  raises an error.
- In salary rules, read the value with
  ``current_contract.advantages.[ADVANTAGE_CODE]``.
