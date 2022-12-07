# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields

_logger = logging.getLogger(__name__)


class BaseBrowsableObject(object):
    def __init__(self, vals_dict):
        self.__dict__["base_fields"] = ["base_fields", "dict"]
        self.dict = vals_dict

    def __getattr__(self, attr):
        return attr in self.dict and self.dict.__getitem__(attr) or 0.0

    def __setattr__(self, attr, value):
        _fields = self.__dict__["base_fields"]
        if attr in _fields:
            return super().__setattr__(attr, value)
        self.__dict__["dict"][attr] = value

    def __str__(self):
        return str(self.__dict__)


# These classes are used in the _get_payslip_lines() method
class BrowsableObject(BaseBrowsableObject):
    def __init__(self, employee_id, vals_dict, env):
        super().__init__(vals_dict)
        self.base_fields += ["employee_id", "env"]
        self.employee_id = employee_id
        self.env = env


class InputLine(BrowsableObject):
    """a class that will be used into the python code, mainly for
    usability purposes"""

    def sum(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(
            """
            SELECT sum(amount) as sum
            FROM hr_payslip as hp, hr_payslip_input as pi
            WHERE hp.employee_id = %s AND hp.state = 'done'
            AND hp.date_from >= %s AND hp.date_to <= %s
            AND hp.id = pi.payslip_id AND pi.code = %s""",
            (self.employee_id, from_date, to_date, code),
        )
        return self.env.cr.fetchone()[0] or 0.0


class WorkedDays(BrowsableObject):
    """a class that will be used into the python code, mainly for
    usability purposes"""

    def _sum(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(
            """
            SELECT sum(number_of_days) as number_of_days,
             sum(number_of_hours) as number_of_hours
            FROM hr_payslip as hp, hr_payslip_worked_days as pi
            WHERE hp.employee_id = %s AND hp.state = 'done'
            AND hp.date_from >= %s AND hp.date_to <= %s
            AND hp.id = pi.payslip_id AND pi.code = %s""",
            (self.employee_id, from_date, to_date, code),
        )
        return self.env.cr.fetchone()

    def sum(self, code, from_date, to_date=None):
        res = self._sum(code, from_date, to_date)
        return res and res[0] or 0.0

    def sum_hours(self, code, from_date, to_date=None):
        res = self._sum(code, from_date, to_date)
        return res and res[1] or 0.0


class Payslips(BrowsableObject):
    """a class that will be used into the python code, mainly for
    usability purposes"""

    def sum_rule(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(
            """SELECT sum(case when hp.credit_note = False then
            (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND
                     hp.id = pl.slip_id AND pl.code = %s""",
            (self.employee_id, from_date, to_date, code),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def sum(self, code, from_date, to_date=None):
        _logger.warning(
            "Payslips Object: sum() method is DEPRECATED. Use sum_rule() instead."
        )
        return self.sum_rule(code, from_date, to_date)

    def average_rule(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(
            """SELECT avg(case when hp.credit_note = False then
            (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND
                     hp.id = pl.slip_id AND pl.code = %s""",
            (self.employee_id, from_date, to_date, code),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def average_rule_monthly(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(
            """SELECT avg(total) FROM (SELECT max(case when hp.credit_note = False then
            (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND
                     hp.id = pl.slip_id AND pl.code = %s) AS monthly_sum""",
            (self.employee_id, from_date, to_date, code),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def max_rule(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(
            """SELECT max(case when hp.credit_note = False then
            (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND
                     hp.id = pl.slip_id AND pl.code = %s""",
            (self.employee_id, from_date, to_date, code),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def max_rule_monthly(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(
            """SELECT max(total) FROM (SELECT max(case when hp.credit_note = False then
            (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND
                     hp.id = pl.slip_id AND pl.code = %s) AS monthly_sum""",
            (self.employee_id, from_date, to_date, code),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def min_rule(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(
            """SELECT min(case when hp.credit_note = False then
            (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND
                     hp.id = pl.slip_id AND pl.code = %s""",
            (self.employee_id, from_date, to_date, code),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def min_rule_monthly(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(
            """SELECT min(total) FROM (SELECT max(case when hp.credit_note = False then
            (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND
                     hp.id = pl.slip_id AND pl.code = %s) AS monthly_sum""",
            (self.employee_id, from_date, to_date, code),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def sum_category(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()

        hierarchy_codes = (
            self.env["hr.salary.rule.category"]
            .search([("code", "=", code)])
            .children_ids.mapped("code")
        )
        hierarchy_codes.append(code)

        self.env.cr.execute(
            """SELECT sum(case when hp.credit_note is not True then
            (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule_category as rc
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id
                    AND rc.id = pl.category_id AND rc.code in %s""",
            (self.employee_id, from_date, to_date, tuple(hierarchy_codes)),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def average_category(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()

        hierarchy_codes = (
            self.env["hr.salary.rule.category"]
            .search([("code", "=", code)])
            .children_ids.mapped("code")
        )
        hierarchy_codes.append(code)

        self.env.cr.execute(
            """SELECT avg(case when hp.credit_note is not True then
            (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule_category as rc
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id
                    AND rc.id = pl.category_id AND rc.code in %s""",
            (self.employee_id, from_date, to_date, tuple(hierarchy_codes)),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def average_category_monthly(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()

        hierarchy_codes = (
            self.env["hr.salary.rule.category"]
            .search([("code", "=", code)])
            .children_ids.mapped("code")
        )
        hierarchy_codes.append(code)

        self.env.cr.execute(
            """SELECT avg(total) FROM (
                SELECT DATE_TRUNC('month',hp.date_from) AS date_month,
                    sum(case when hp.credit_note is not True then
                        (pl.total) else (-pl.total) end) AS total
                FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule_category as rc
                WHERE hp.employee_id = %s AND hp.state = 'done'
                AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id
                AND rc.id = pl.category_id AND rc.code in %s
                GROUP BY date_month) AS monthly_sum""",
            (self.employee_id, from_date, to_date, tuple(hierarchy_codes)),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def max_category(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()

        hierarchy_codes = (
            self.env["hr.salary.rule.category"]
            .search([("code", "=", code)])
            .children_ids.mapped("code")
        )
        hierarchy_codes.append(code)

        self.env.cr.execute(
            """SELECT max(case when hp.credit_note is not True then
            (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule_category as rc
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id
                    AND rc.id = pl.category_id AND rc.code in %s""",
            (self.employee_id, from_date, to_date, tuple(hierarchy_codes)),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def max_category_monthly(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()

        hierarchy_codes = (
            self.env["hr.salary.rule.category"]
            .search([("code", "=", code)])
            .children_ids.mapped("code")
        )
        hierarchy_codes.append(code)

        self.env.cr.execute(
            """SELECT max(total) FROM (
                SELECT DATE_TRUNC('month',hp.date_from) AS date_month,
                    sum(case when hp.credit_note is not True then
                        (pl.total) else (-pl.total) end) AS total
                FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule_category as rc
                WHERE hp.employee_id = %s AND hp.state = 'done'
                AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id
                AND rc.id = pl.category_id AND rc.code in %s
                GROUP BY date_month) AS monthly_sum""",
            (self.employee_id, from_date, to_date, tuple(hierarchy_codes)),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def min_category(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()

        hierarchy_codes = (
            self.env["hr.salary.rule.category"]
            .search([("code", "=", code)])
            .children_ids.mapped("code")
        )
        hierarchy_codes.append(code)

        self.env.cr.execute(
            """SELECT min(case when hp.credit_note is not True then
            (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule_category as rc
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id
                    AND rc.id = pl.category_id AND rc.code in %s""",
            (self.employee_id, from_date, to_date, tuple(hierarchy_codes)),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def min_category_monthly(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()

        hierarchy_codes = (
            self.env["hr.salary.rule.category"]
            .search([("code", "=", code)])
            .children_ids.mapped("code")
        )
        hierarchy_codes.append(code)

        self.env.cr.execute(
            """SELECT min(total) FROM (
                SELECT DATE_TRUNC('month',hp.date_from) AS date_month,
                    sum(case when hp.credit_note is not True then
                        (pl.total) else (-pl.total) end) AS total
                FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule_category as rc
                WHERE hp.employee_id = %s AND hp.state = 'done'
                AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id
                AND rc.id = pl.category_id AND rc.code in %s
                GROUP BY date_month) AS monthly_sum""",
            (self.employee_id, from_date, to_date, tuple(hierarchy_codes)),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0
