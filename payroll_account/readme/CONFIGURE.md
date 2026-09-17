Each salary rule carries its own accounting configuration, under *Payroll >
Configuration > Salary Rules*, tab *Accounting*:

- **Debit Account** and **Credit Account**. A rule with neither generates no
  journal item at all; a rule with only one generates a single item, and the
  difference is balanced on the journal's default account (see below). Both
  accounts are **company-dependent**: in a multi-company database, configure
  them once per company.
- **Analytic Account**, when analytic accounting is enabled. The contract's
  analytic account takes precedence over the rule's.
- **Tax** and **Base**, to let the generated items carry the tax, its
  repartition line and its tax grids.

The journal the entry lands in is taken from, in order of precedence:

1. the **payslip's own journal**, which can be changed on the payslip;
2. the **batch's journal** (*Salary Journal* on the payslip batch), which is
   what the payslips of a batch are created with;
3. the **contract's journal** (*Accounting* group of the contract form).

Give that journal a **default account** (*Accounting > Configuration >
Journals*): it is the account the payslip's rounding/adjustment item is booked
on whenever the rules alone do not balance. Without it, confirming such a
payslip raises an error.
