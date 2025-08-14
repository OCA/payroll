from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # in v13, these fields were not company_dependent
    if openupgrade.column_exists(env.cr, "hr_salary_rule", "account_debit"):
        field_names = ["account_debit"]
        if openupgrade.column_exists(env.cr, "hr_salary_rule", "account_credit"):
            field_names += ["account_credit"]
        openupgrade.rename_columns(
            env.cr,
            {"hr_salary_rule": [(field_name, None) for field_name in field_names]},
        )
        openupgrade.rename_columns(
            env.cr,
            {"hr_payslip_line": [(field_name, None) for field_name in field_names]},
        )
