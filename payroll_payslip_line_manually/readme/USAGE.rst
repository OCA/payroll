Usage Demo
----------

* In the menu, go to Employees - Employees - Contracts and open a contract.
* Click on Salary Information and select Analytic Structure.
* Click on Salary Rules, add a line and select Fixed hourly wage, and set a quantity.
* The same rule may be on multiple lines, with different analytic account.
*
* In the menu, go to Payroll - Employee Payslips and open a payslip.
* Select the contract, and Analytic Structure.
* Under Salary Rules, add a line, select Hourly wage, and set a quantity and amount (price).
* The same rule may be on multiple lines, with different analytic account.
*
* Click on Compute Sheet and see the Salary Computation.

Usage in Salary Rule
--------------------

Salary Rule input from Contract or Payslip

Python Condition

```record = contract.line_manually_ids
if record:
    record = record.filtered(lambda x: x.salary_rule_id.id == rule.id)
result = bool(record)```

Python Code

```result_list = []
records = contract.line_manually_ids.filtered(
    lambda x: x.salary_rule_id.id == rule.id
)
for record in records:
    result_list.append(
        record.get_result_dict(
            # optional arguments:
            # months=1.5 (float),
            # multiply_with="result_qty" or "result_rate",
            # uom="hours" (string),
            # default_amount=10.0 (float),
        )
    )```

This code is for a contract rule. For a payslip rule, replace `contract` with `payslip`.

Usage in Contract or Payslip
----------------------------

* A) In the menu, go to Employees - Employees - Contracts and open a contract.
* B) In the menu, go to Payroll - Employee Payslips and open a payslip.
* Go to Salary Rules, add a line and set Salary Rule and Quantity.
* Analytic Account and Amount is optional (see the default_amount argument).
