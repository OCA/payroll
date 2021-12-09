# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(
        env.cr, "payroll", "migrations/13.0.1.0.2/noupdate_changes.xml"
    )
    # Delete the domain defined in previous versions
    env.ref("payroll.open_payroll_modules").domain = False
