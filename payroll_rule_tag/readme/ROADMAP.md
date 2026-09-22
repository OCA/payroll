- The `name_company_unique` SQL constraint compares the whole translated
  value of the name, so it only rejects tags that are duplicated in every
  language. Uniqueness that actually matters for computations is enforced by
  the effective code constraint.
- `hr.payslip.line` inherits the Tags field from `hr.salary.rule`, but no
  view exposes it on payslip lines yet. Reporting payslip lines grouped by
  tag would be a natural next step.
