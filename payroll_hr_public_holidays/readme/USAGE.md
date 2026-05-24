- Set public holidays via the **Public Holidays** menu provided by
  `calendar_public_holiday` (model `calendar.public.holiday`). This is
  the source read by this module to produce the `PHOL` line on payslips.
- Do not use the **Public Holidays** menu provided by Odoo standard
  `hr_holidays`: it stores entries on `resource.calendar.leaves` which
  are not picked up here and produce a generic line on the payslip
  instead of a `PHOL` line.
- Create a payslip: public holidays from `calendar.public.holiday` are
  fetched automatically into the worked days table with code `PHOL`.
