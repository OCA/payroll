from odoo.addons.payroll.migrations.move_records import move_records


def pre_init_hook(cr):
    cr.execute(
        """
        SELECT count(tablename) FROM pg_tables
        WHERE tablename LIKE 'openupgrade_legacy_14_0_hr_rule_parameter%';"""
    )
    if cr.fetchone()[0]:
        move_records(cr, legacy=True)
