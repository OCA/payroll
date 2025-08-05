from openupgradelib import openupgrade, openupgrade_180


@openupgrade.migrate()
def migrate(env, version):
    openupgrade_180.convert_company_dependent(env, "hr.salary.rule", "account_debit")
    openupgrade_180.convert_company_dependent(env, "hr.salary.rule", "account_credit")
