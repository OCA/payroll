from openupgradelib import openupgrade

field_names = ["account_debit", "account_credit"]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_columns(
        env.cr,
        {"hr_salary_rule": [(field_name, None) for field_name in field_names]},
    )
