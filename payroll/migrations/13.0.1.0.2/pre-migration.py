# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

xmlid_renames = [
    (
        "hr_payroll.act_contribution_reg_payslip_lines",
        "hr_payroll.hr_payslip_line_action",
    ),
    (
        "hr_payroll.act_hr_employee_payslip_list",
        "hr_payroll.hr_payslip_action_employee",
    ),
    (
        "hr_payroll.act_payslip_lines",
        "hr_payroll.hr_payslip_line_action_computation_details",
    ),
    (
        "hr_payroll.action_contribution_register_form",
        "hr_payroll.hr_contribution_register_action",
    ),
    (
        "hr_payroll.action_hr_payroll_configuration",
        "hr_payroll.payroll_configuration_action",
    ),
    ("hr_payroll.action_hr_payslip_run_tree", "hr_payroll.hr_payslip_run_action"),
    (
        "hr_payroll.action_hr_salary_rule_category",
        "hr_payroll.hr_salary_rule_category_action",
    ),
    (
        "hr_payroll.action_view_hr_payroll_structure_list_form",
        "hr_payroll.hr_payroll_structure_action",
    ),
    ("hr_payroll.action_view_hr_payslip_form", "hr_payroll.hr_payslip_action"),
    (
        "hr_payroll.menu_action_hr_contribution_register_form",
        "hr_payroll.hr_contribution_register_menu",
    ),
    ("hr_payroll.menu_department_tree", "hr_payroll.hr_payslip_menu"),
    (
        "hr_payroll.menu_hr_payroll_configuration",
        "hr_payroll.payroll_menu_configuration",
    ),
    (
        "hr_payroll.menu_hr_payroll_global_settings",
        "hr_payroll.menu_payroll_global_settings",
    ),
    ("hr_payroll.menu_hr_payroll_root", "hr_payroll.payroll_menu_root",),
    (
        "hr_payroll.menu_hr_payroll_structure_view",
        "hr_payroll.hr_payroll_structure_menu",
    ),
    ("hr_payroll.menu_hr_payslip_run", "hr_payroll.hr_payslip_run_menu"),
    ("hr_payroll.hr_contract_form_inherit", "hr_payroll.hr_contract_view_form"),
    (
        "hr_payroll.hr_contribution_register_filter",
        "hr_payroll.hr_contribution_register_view_search",
    ),
    (
        "hr_payroll.hr_contribution_register_form",
        "hr_payroll.hr_contribution_register_view_form",
    ),
    (
        "hr_payroll.hr_contribution_register_tree",
        "hr_payroll.hr_contribution_register_view_tree",
    ),
    ("hr_payroll.hr_payslip_run_filter", "hr_payroll.hr_payslip_run_view_search"),
    ("hr_payroll.hr_payslip_run_form", "hr_payroll.hr_payslip_run_view_form"),
    ("hr_payroll.hr_payslip_run_tree", "hr_payroll.hr_payslip_run_view_tree"),
    (
        "hr_payroll.hr_salary_rule_category_form",
        "hr_payroll.hr_salary_rule_category_view_form",
    ),
    (
        "hr_payroll.hr_salary_rule_category_tree",
        "hr_payroll.hr_salary_rule_category_view_tree",
    ),
    ("hr_payroll.hr_salary_rule_form", "hr_payroll.hr_salary_rule_view_form"),
    ("hr_payroll.hr_salary_rule_list", "hr_payroll.hr_salary_rule_view_tree_children"),
    ("hr_payroll.hr_salary_rule_tree", "hr_payroll.hr_salary_rule_view_tree"),
    ("hr_payroll.payroll_hr_employee_view_form", "hr_payroll.hr_employee_view_form"),
    (
        "hr_payroll.view_hr_employee_grade_form",
        "hr_payroll.hr_payroll_structure_view_form",
    ),
    (
        "hr_payroll.view_hr_payroll_structure_filter",
        "hr_payroll.hr_payroll_structure_view_search",
    ),
    (
        "hr_payroll.view_hr_payroll_structure_list_view",
        "hr_payroll.hr_payroll_structure_view_tree",
    ),
    (
        "hr_payroll.view_hr_payroll_structure_tree",
        "hr_payroll.hr_payroll_structure_view_tree_children",
    ),
    ("hr_payroll.view_hr_payslip_filter", "hr_payroll.hr_payslip_view_search"),
    ("hr_payroll.view_hr_payslip_form", "hr_payroll.hr_payslip_view_form"),
    (
        "hr_payroll.view_hr_payslip_line_filter",
        "hr_payroll.hr_payslip_line_view_search",
    ),
    ("hr_payroll.view_hr_payslip_line_form", "hr_payroll.hr_payslip_line_view_form"),
    ("hr_payroll.view_hr_payslip_line_tree", "hr_payroll.hr_payslip_line_view_tree"),
    ("hr_payroll.view_hr_payslip_tree", "hr_payroll.hr_payslip_view_tree"),
    ("hr_payroll.view_hr_rule_filter", "hr_payroll.hr_salary_rule_view_search"),
    (
        "hr_payroll.view_hr_salary_rule_category_filter",
        "hr_payroll.hr_salary_rule_category_view_search",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_xmlids(env.cr, xmlid_renames)
