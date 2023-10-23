from odoo.tools.sql import column_exists, rename_column


def migrate(cr, version):
    if column_exists(cr, "hr_contract", "shedule_pay"):
        rename_column(
            cr,
            "hr_contract",
            "shedule_pay",
            "schedule_pay",
        )
