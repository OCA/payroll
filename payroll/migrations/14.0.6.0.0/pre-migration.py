from openupgradelib import openupgrade


def move_records(env):
    """
    hr.rule.parameter -> base.time.parameter
    hr.rule.parameter.value -> base.time.parameter.version
        (with new id for many2one base.time.parameter)
    """

    payslip_model_id = env["ir.model"].search([("model", "=", "hr.payslip")]).id

    sql_select_parameters = """
    SELECT id, name, code, description, company_id, country_id, 'text'
    FROM hr_rule_parameter
    """
    env.cr.execute(sql_select_parameters)
    parameters = [(p[0], p[1:] + (payslip_model_id,)) for p in env.cr.fetchall()]

    sql_insert_parameters = """
    INSERT INTO base_time_parameter (
        name, code, description, company_id, country_id, type, model_id
    )
    VALUES {parameters}
    RETURNING id;
    """.format(
        parameters=", ".join([str(p[1]).replace("None", "null") for p in parameters]),
    )
    env.cr.execute(sql_insert_parameters)
    new_parameters = env.cr.fetchall()
    id_old_new = {}
    for i in range(len(parameters)):
        id_old_new[parameters[i][0]] = new_parameters[i][0]

    sql_select_versions = """
    SELECT pv.rule_parameter_id, p.company_id, pv.code, pv.date_from, pv.parameter_value
    FROM hr_rule_parameter_value pv JOIN hr_rule_parameter p
        ON pv.rule_parameter_id = p.id;
    """
    env.cr.execute(sql_select_versions)
    versions = [
        (id_old_new[v[0]], v[1], v[2], v[3].strftime("%Y-%m-%d"), v[4])
        for v in env.cr.fetchall()
    ]

    sql_insert_versions = """
    INSERT INTO base_time_parameter_version (
        parameter_id, company_id, code, date_from, value_text
    )
    VALUES {versions}
    """.format(
        versions=", ".join([str(v) for v in versions])
    )
    env.cr.execute(sql_insert_versions)


@openupgrade.migrate()
def migrate(env, version):
    move_records(env)
