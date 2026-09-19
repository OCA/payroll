Provides an abstract sync mechanism that creates a
``hr.contract.advantage`` from each applicable
``hr.contract.advantage.template`` on a contract. The mechanism is
additive only: existing advantages on the contract are never removed
nor overwritten.

This base module does not select any template by itself. It exposes a
hook to be plugged by bridge modules, which can attach templates to
the criterion that fits their needs, for example:

- by salary structure: an advantage applies to all employees on a
  given salary structure (e.g. company car for executives);
- by employee tag (``hr.employee.category``): an advantage applies to
  every employee tagged accordingly (e.g. meal voucher for on-site
  staff);
- by department: an advantage applies to a whole department (e.g.
  IT support stipend);
- by job position: an advantage applies to a specific position;
- by company, country, or any other criterion the integrator needs.

Each criterion is implemented by its own small bridge module that
overrides the hook and provides the relevant trigger.
