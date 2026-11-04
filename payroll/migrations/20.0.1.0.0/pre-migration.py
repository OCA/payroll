# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from openupgradelib import openupgrade

_model_renames = [
    ("hr.payslip", "payroll.payslip"),
    ("hr.payslip.line", "payroll.payslip.line"),
    ("hr.payslip.input", "payroll.payslip.input"),
    ("hr.payslip.run", "payroll.payslip.run"),
    ("hr.payslip.worked_days", "payroll.payslip.worked_days"),
    ("hr.salary.rule", "payroll.salary.rule"),
    ("hr.salary.rule.category", "payroll.salary.rule.category"),
    ("hr.payroll.structure", "payroll.structure"),
    ("hr.contribution.register", "payroll.contribution.register"),
    ("hr.rule.input", "payroll.rule.input"),
    ("hr.payslip.employees", "payroll.payslip.employees"),
    ("hr.payslip.change.state", "payroll.payslip.change.state"),
    ("payslip.lines.contribution.register", "payroll.lines.contribution.register"),
]

_table_renames = [
    ("hr_payslip", "payroll_payslip"),
    ("hr_payslip_line", "payroll_payslip_line"),
    ("hr_payslip_input", "payroll_payslip_input"),
    ("hr_payslip_run", "payroll_payslip_run"),
    ("hr_payslip_worked_days", "payroll_payslip_worked_days"),
    ("hr_salary_rule", "payroll_salary_rule"),
    ("hr_salary_rule_category", "payroll_salary_rule_category"),
    ("hr_payroll_structure", "payroll_structure"),
    ("hr_contribution_register", "payroll_contribution_register"),
    ("hr_rule_input", "payroll_rule_input"),
    ("hr_payslip_employees", "payroll_payslip_employees"),
    ("hr_payslip_change_state", "payroll_payslip_change_state"),
    (
        "payslip_lines_contribution_register",
        "payroll_lines_contribution_register",
    ),
    ("hr_structure_salary_rule_rel", "payroll_structure_salary_rule_rel"),
]

_field_renames = [
    ("hr.version", "hr_version", "struct_id", "payroll_struct_id"),
    ("hr.version", "hr_version", "schedule_pay", "payroll_schedule_pay"),
    ("hr.employee", "hr_employee", "slip_ids", "payroll_slip_ids"),
    ("hr.employee", "hr_employee", "payslip_count", "payroll_slip_count"),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_models(env.cr, _model_renames)
    openupgrade.rename_tables(env.cr, _table_renames)
    openupgrade.rename_fields(env, _field_renames)
