Configuration
==============

Dependencies
~~~~~~~~~~~~
This module depends on:

* **HR Payroll Period** (payroll periods and *Date of Payment* on payslips).
* **Payroll Accounting** (journal, accounting entry and move lines from payslips).

No extra configuration is required for the module to work: once both are
installed and set up, payment status and due dates on payable/receivable
lines are applied automatically.

Optional: use payable/receivable accounts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For **Payment Status** and **Due date** to apply on the payslip’s accounting
entry:

1. Go to **Payroll → Configuration → Salary Rules**.
2. Open the rules that should drive payment tracking (e.g. net salary).
3. In the **Accounting** tab, set **Credit Account** (and/or **Debit Account**)
   to an account of type **Payable** or **Receivable** where appropriate.

Move lines that use other account types (e.g. expense, bank) are not used for
payment status and do not get their due date updated from the payslip’s
*Date of Payment*.

Payment date on the payslip
~~~~~~~~~~~~~~~~~~~~~~~~~~~
*Date of Payment* is usually set from the payroll period (when you select a
period or create payslips from a batch). You can also set or adjust it
manually on the payslip while it is in draft. That date is the one used to
fill the due date on payable/receivable move lines when the payslip is
confirmed.
