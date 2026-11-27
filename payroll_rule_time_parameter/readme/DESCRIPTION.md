This module adds Rule Parameters to the payroll configuration menu: values
that depend on a date, looked up from the salary rule that needs them.

Use in salary rule python code like this:

``` python
# Value of the parameter at the start date of the payslip
myvalue = payslip.rule_parameter("mycode")
# Value at another date
myvalue = payslip.rule_parameter("mycode", date=payslip.date_to)
# Start date of the version the value comes from
mydate = payslip.rule_parameter("mycode", get="date")
```
