Salary Tables are maintained at Payroll / Configuration / Salary Tables.
Create a Salary Table Period to create a table valid for a specific period.

On a Salary Table Period set:

- Template: the salary table being used
- Company : the company it applies to (all if left empty)
- Start and End Dates: the validity period (optional)
- Note: any comment and notes
- Lines: enter each combination and the Result value to be used when matched

Salary Tables can accessed in salary rules using the ``lookup_table`` function.
Examples:
```
value = lookup_table("BASIC")
rate = lookup_table("TAX", taxable_amount)
```

Master Data values can be accessed in salary rules using the get_data_value function.
Examples:
```
result = contract.get_data_value("BASIC")
result_data = contract.get_data_value("TAX_SITUATION")
```

Payslip lines can store a Master Data value returned by a salary rule
in the ``result_data`` variable. This can be useful for audit and reporting.
