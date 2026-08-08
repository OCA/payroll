Create a parameter under **Payroll → Configuration → Rule Parameters**, give it a
code, and add one value per date the figure changes.

A value can be a number:

    0.0192

or a structure, such as a list of tax brackets:

    [(0.0, 0.0, 0.0192), (7735.0, 148.51, 0.064), (65651.07, 3866.42, 0.1088)]

Read it from a salary rule with the payslip's own date:

    brackets = payslip.rule_parameter("income_tax_brackets")
    base = categories.GROSS
    for lower_limit, fixed_fee, rate in reversed(brackets):
        if base > lower_limit:
            result = -(fixed_fee + (base - lower_limit) * rate)
            break

`payslip.rule_parameter()` resolves the value in force on the payslip's
`date_to`, so recomputing a past payslip uses the rates of that period.
