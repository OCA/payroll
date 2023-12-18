# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

xmlid_renames = [
    ("payroll.act_contribution_reg_payslip_lines", "payroll.hr_payslip_line_action",),
    ("payroll.act_hr_employee_payslip_list", "payroll.hr_payslip_action_employee",),
    (
        "payroll.act_payslip_lines",
        "payroll.hr_payslip_line_action_computation_details",
    ),
    (
        "payroll.action_contribution_register_form",
        "payroll.hr_contribution_register_action",
    ),
    (
        "payroll.action_hr_payroll_configuration",
        "payroll.payroll_configuration_action",
    ),
    ("payroll.action_hr_payslip_run_tree", "payroll.hr_payslip_run_action"),
    (
        "payroll.action_hr_salary_rule_category",
        "payroll.hr_salary_rule_category_action",
    ),
    (
        "payroll.action_view_hr_payroll_structure_list_form",
        "payroll.hr_payroll_structure_action",
    ),
    ("payroll.action_view_hr_payslip_form", "payroll.hr_payslip_action"),
    (
        "payroll.menu_action_hr_contribution_register_form",
        "payroll.hr_contribution_register_menu",
    ),
    ("payroll.menu_department_tree", "payroll.hr_payslip_menu"),
    ("payroll.menu_hr_payroll_configuration", "payroll.payroll_menu_configuration",),
    (
        "payroll.menu_hr_payroll_global_settings",
        "payroll.menu_payroll_global_settings",
    ),
    ("payroll.menu_hr_payroll_root", "payroll.payroll_menu_root",),
    ("payroll.menu_hr_payroll_structure_view", "payroll.hr_payroll_structure_menu",),
    ("payroll.menu_hr_payslip_run", "payroll.hr_payslip_run_menu"),
    ("payroll.hr_contract_form_inherit", "payroll.hr_contract_view_form"),
    (
        "payroll.hr_contribution_register_filter",
        "payroll.hr_contribution_register_view_search",
    ),
    (
        "payroll.hr_contribution_register_form",
        "payroll.hr_contribution_register_view_form",
    ),
    (
        "payroll.hr_contribution_register_tree",
        "payroll.hr_contribution_register_view_tree",
    ),
    ("payroll.hr_payslip_run_filter", "payroll.hr_payslip_run_view_search"),
    ("payroll.hr_payslip_run_form", "payroll.hr_payslip_run_view_form"),
    ("payroll.hr_payslip_run_tree", "payroll.hr_payslip_run_view_tree"),
    (
        "payroll.hr_salary_rule_category_form",
        "payroll.hr_salary_rule_category_view_form",
    ),
    (
        "payroll.hr_salary_rule_category_tree",
        "payroll.hr_salary_rule_category_view_tree",
    ),
    ("payroll.hr_salary_rule_form", "payroll.hr_salary_rule_view_form"),
    ("payroll.hr_salary_rule_list", "payroll.hr_salary_rule_view_tree_children"),
    ("payroll.hr_salary_rule_tree", "payroll.hr_salary_rule_view_tree"),
    ("payroll.payroll_hr_employee_view_form", "payroll.hr_employee_view_form"),
    ("payroll.view_hr_employee_grade_form", "payroll.hr_payroll_structure_view_form",),
    (
        "payroll.view_hr_payroll_structure_filter",
        "payroll.hr_payroll_structure_view_search",
    ),
    (
        "payroll.view_hr_payroll_structure_list_view",
        "payroll.hr_payroll_structure_view_tree",
    ),
    (
        "payroll.view_hr_payroll_structure_tree",
        "payroll.hr_payroll_structure_view_tree_children",
    ),
    ("payroll.view_hr_payslip_filter", "payroll.hr_payslip_view_search"),
    ("payroll.view_hr_payslip_form", "payroll.hr_payslip_view_form"),
    ("payroll.view_hr_payslip_line_filter", "payroll.hr_payslip_line_view_search",),
    ("payroll.view_hr_payslip_line_form", "payroll.hr_payslip_line_view_form"),
    ("payroll.view_hr_payslip_line_tree", "payroll.hr_payslip_line_view_tree"),
    ("payroll.view_hr_payslip_tree", "payroll.hr_payslip_view_tree"),
    ("payroll.view_hr_rule_filter", "payroll.hr_salary_rule_view_search"),
    (
        "payroll.view_hr_salary_rule_category_filter",
        "payroll.hr_salary_rule_category_view_search",
    ),
    ("payroll.group_hr_payroll_manager", "payroll.group_payroll_manager",),
    ("payroll.group_hr_payroll_user", "payroll.group_payroll_user",),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_xmlids(env.cr, xmlid_renames)
