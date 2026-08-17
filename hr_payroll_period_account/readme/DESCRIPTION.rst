Payroll period and accounting integration.

This module bridges **HR Payroll Period** and **Payroll Accounting** so that:

* **Payment date on move lines**  
  When a payslip is confirmed, the *Date of Payment* (from the payroll period or
  the payslip) is written to the **Due date** (`date_maturity`) of all
  accounting move lines that use **Payable** or **Receivable** accounts. Other
  account types are left unchanged.

* **Payment status on payslips**  
  A computed **Payment Status** field is added to payslips:

  * **Paid** when every payable/receivable line of the related accounting entry
    is fully reconciled.
  * **Not Paid** when at least one such line is not reconciled.
  * Empty when there is no accounting entry or no payable/receivable lines.

* **Visibility**  
  Payment status is shown as a badge (green for Paid, red for Not Paid) in the
  payslip list view and in the Accounting Information section of the payslip
  form.

You need both **HR Payroll Period** (for payment dates and periods) and
**Payroll Accounting** (for journal and move) installed.
