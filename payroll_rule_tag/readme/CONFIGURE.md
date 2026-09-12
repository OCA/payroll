Salary rule Tags can be defined from the Payroll / Configuration menu,
and are assigned to Salary Rules using the "Tags" field in the Computation form area.

Each tag has:

- a **Name**, used as the tag label,
- an optional **Code**, the identifier salary rules use to read the tag
  total. When left empty, the code is the name in uppercase, with anything
  that is not a letter, a number or an underscore replaced by an underscore
  (so "Taxable Income" gives `TAXABLE_INCOME`),
- a **Company**, since tags are company specific,
- a **Sequence** and a **Color**, used for ordering and display only.

Two tags of the same company cannot resolve to the same code, otherwise
salary rules would not be able to tell their totals apart.
