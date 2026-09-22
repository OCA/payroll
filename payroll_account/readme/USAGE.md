Confirming a payslip generates **one** accounting entry, posted in the
payslip's journal, and links it to the payslip -- the *Journal Entry* button on
the payslip form opens it. Every salary rule with a debit and/or a credit
account contributes an item; the entry is dated with the payslip's *Date
Account*, falling back to the end of the period.

Partners are set only on the items whose account tracks an external
relationship: the employee on receivable and current-liability accounts, the
contribution register's partner on payable ones. Expense and income items carry
no partner.

Confirming an already-confirmed payslip does nothing: the payslip keeps the
entry it already has, instead of booking every amount twice.

**Cancelling** a payslip does not delete its entry. A posted entry is reversed,
and both the entry and its reversal stay attached to the payslip for the audit
trail; an entry that was never posted is simply dropped. Confirming the payslip
again generates a new entry. A payslip that still carries a posted entry cannot
be deleted -- cancel it first.

A **refund** (*Refund* on a confirmed payslip) is an ordinary payslip with
inverted amounts, so it generates its own entry, with debits and credits the
other way round.
