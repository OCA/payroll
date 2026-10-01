Salary rule Tags can be defined from the Payroll / Configuration menu,
and are assigned to Salary Rules using the "Tags" field in the Computation form area.

Each tag has:

- a **Name**, used as the tag label,
- a **Code**, the identifier salary rules use to read the tag total
  (`tags.<CODE>`). It is required, and proposed from the name while it is
  empty: the name in uppercase, with anything that is not a letter, a number
  or an underscore replaced by an underscore (so "Taxable Income" gives
  `TAXABLE_INCOME`). Renaming a tag keeps its code,
- a **Company**, since tags are company specific,
- a **Sequence** and a **Color**, used for ordering and display only.

The code is unique per company, otherwise salary rules would not be able to
tell the totals apart. The name is free text.
