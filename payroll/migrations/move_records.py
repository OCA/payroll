from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api


@openupgrade.logging()
def move_records(cr, legacy):
    """
    hr.rule.parameter -> base.time.parameter
    hr.rule.parameter.value -> base.time.parameter.version
        (with new id for many2one base.time.parameter)
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    payslip_model_id = env["ir.model"].search([("model", "=", "hr.payslip")]).id

    name = "openupgrade_legacy_14_0_" if legacy else ""
    hr_rule_parameter = name + "hr_rule_parameter"
    hr_rule_parameter_value = name + "hr_rule_parameter_value"

    sql_select_parameters = """
    SELECT id, name, code, description, company_id, country_id, 'text'
    FROM {hr_rule_parameter}
    """.format(
        hr_rule_parameter=hr_rule_parameter
    )
    openupgrade.logged_query(cr, sql_select_parameters)
    parameters = [(p[0], p[1:] + (payslip_model_id,)) for p in cr.fetchall()]

    sql_insert_parameters = """
    INSERT INTO base_time_parameter (
        name, code, description, company_id, country_id, type, model_id
    )
    VALUES {parameters}
    RETURNING id;
    """.format(
        parameters=", ".join([str(p[1]).replace("None", "null") for p in parameters]),
    )
    openupgrade.logged_query(cr, sql_insert_parameters)
    new_parameters = cr.fetchall()
    id_old_new = {}
    for i in range(len(parameters)):
        id_old_new[parameters[i][0]] = new_parameters[i][0]

    sql_select_versions = """
    SELECT pv.rule_parameter_id, p.company_id, pv.code, pv.date_from, pv.parameter_value
    FROM {hr_rule_parameter_value} pv JOIN {hr_rule_parameter} p
        ON pv.rule_parameter_id = p.id;
    """.format(
        hr_rule_parameter_value=hr_rule_parameter_value,
        hr_rule_parameter=hr_rule_parameter,
    )
    openupgrade.logged_query(cr, sql_select_versions)
    versions = [
        (id_old_new[v[0]], v[1], v[2], v[3].strftime("%Y-%m-%d"), v[4])
        for v in cr.fetchall()
    ]

    sql_insert_versions = """
    INSERT INTO base_time_parameter_version (
        parameter_id, company_id, code, date_from, value
    )
    VALUES {versions}
    """.format(
        versions=", ".join([str(v) for v in versions])
    )
    openupgrade.logged_query(cr, sql_insert_versions)
