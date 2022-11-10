from openupgradelib import openupgrade

from odoo.addons.payroll.migrations.move_records import move_records


def rename_tables(cr):
    openupgrade.rename_tables(
        cr,
        [
            ("hr_rule_parameter", None),
            ("hr_rule_parameter_value", None),
        ],
    )


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    module = env["ir.module.module"].search([("name", "=", "base_time_parameter")])
    if module.exists() and module.state == "installed":
        move_records(cr, legacy=False)
    else:
        rename_tables(cr)
