from odoo import _, fields, models
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    _name = "hr.payslip.employees"
    _description = "Generate payslips for all selected employees"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    department_id = fields.Many2one("hr.department", string="Department")
    job_id = fields.Many2one("hr.job", string="Job Position")
    employee_ids = fields.Many2many(
        "hr.employee", "hr_employee_group_rel", "payslip_id", "employee_id", "Employees"
    )

    def _get_reopen_wizard_action(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": dict(self.env.context),
        }

    def action_apply_employee_filter(self):
        self.ensure_one()
        domain = []
        if self.company_id:
            domain.append(("company_id", "=", self.company_id.id))
        if self.department_id:
            domain.append(("department_id", "=", self.department_id.id))
        if self.job_id:
            domain.append(("job_id", "=", self.job_id.id))
        employee_ids = self.env["hr.employee"].search(domain).ids
        self.write({"employee_ids": [(6, 0, employee_ids)]})
        return self._get_reopen_wizard_action()

    def action_clear_employees(self):
        self.ensure_one()
        self.write({"employee_ids": [(5, 0, 0)]})
        # Preserve originating action context (active_id on hr.payslip.run). A dict
        # return is required: other truthy values become act_window_close in web.
        return self._get_reopen_wizard_action()

    def compute_sheet(self):
        payslips = self.env["hr.payslip"]
        [data] = self.read()
        active_id = self.env.context.get("active_id")
        if active_id:
            [run_data] = (
                self.env["hr.payslip.run"]
                .browse(active_id)
                .read(["date_start", "date_end", "credit_note", "struct_id"])
            )
        from_date = run_data.get("date_start")
        to_date = run_data.get("date_end")
        struct_id = run_data.get("struct_id")
        if not data["employee_ids"]:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in self.env["hr.employee"].browse(data["employee_ids"]):
            slip_data = self.env["hr.payslip"].get_payslip_vals(
                from_date, to_date, employee.id, contract_id=False, struct_id=struct_id
            )
            res = {
                "employee_id": employee.id,
                "name": slip_data["value"].get("name"),
                "struct_id": slip_data["value"].get("struct_id"),
                "contract_id": slip_data["value"].get("contract_id"),
                "payslip_run_id": active_id,
                "input_line_ids": [
                    (0, 0, x) for x in slip_data["value"].get("input_line_ids")
                ],
                "worked_days_line_ids": [
                    (0, 0, x) for x in slip_data["value"].get("worked_days_line_ids")
                ],
                "date_from": from_date,
                "date_to": to_date,
                "credit_note": run_data.get("credit_note"),
                "company_id": employee.company_id.id,
            }
            payslips += self.env["hr.payslip"].create(res)
        payslips._compute_name()
        payslips.compute_sheet()
        return {"type": "ir.actions.act_window_close"}
