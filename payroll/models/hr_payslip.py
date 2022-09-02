# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date, datetime, time

import babel
from dateutil.relativedelta import relativedelta
from pytz import timezone

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError


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

    def sum(self, code, from_date, to_date=None):
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

    def rule_parameter(self, code):
        return self.env["hr.rule.parameter"]._get_parameter_from_code(
            code, self.dict.date_to
        )


class HrPayslip(models.Model):
    _name = "hr.payslip"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Pay Slip"
    _order = "id desc"

    struct_id = fields.Many2one(
        "hr.payroll.structure",
        string="Structure",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Defines the rules that have to be applied to this payslip, "
        "accordingly to the contract chosen. If you let empty the field "
        "contract, this field isn't mandatory anymore and thus the rules "
        "applied will be all the rules set on the structure of all contracts "
        "of the employee valid for the chosen period",
    )
    name = fields.Char(
        string="Payslip Name", readonly=True, states={"draft": [("readonly", False)]}
    )
    number = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        states={"draft": [("readonly", False)]},
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_from = fields.Date(
        string="Date From",
        readonly=True,
        required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
        states={"draft": [("readonly", False)]},
        tracking=True,
    )
    date_to = fields.Date(
        string="Date To",
        readonly=True,
        required=True,
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()
        ),
        states={"draft": [("readonly", False)]},
        tracking=True,
    )
    # this is chaos: 4 states are defined, 3 are used ('verify' isn't) and 5
    # exist ('confirm' seems to have existed)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("verify", "Waiting"),
            ("done", "Done"),
            ("cancel", "Rejected"),
        ],
        string="Status",
        index=True,
        readonly=True,
        copy=False,
        default="draft",
        tracking=True,
        help="""* When the payslip is created the status is \'Draft\'
        \n* If the payslip is under verification, the status is \'Waiting\'.
        \n* If the payslip is confirmed then status is set to \'Done\'.
        \n* When user cancel payslip the status is \'Rejected\'.""",
    )
    line_ids = fields.One2many(
        "hr.payslip.line",
        "slip_id",
        string="Payslip Lines",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        readonly=True,
        copy=False,
        default=lambda self: self.env.company,
        states={"draft": [("readonly", False)]},
    )
    worked_days_line_ids = fields.One2many(
        "hr.payslip.worked_days",
        "payslip_id",
        string="Payslip Worked Days",
        copy=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    input_line_ids = fields.One2many(
        "hr.payslip.input",
        "payslip_id",
        string="Payslip Inputs",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    paid = fields.Boolean(
        string="Made Payment Order ? ",
        readonly=True,
        copy=False,
        states={"draft": [("readonly", False)]},
    )
    note = fields.Text(
        string="Internal Note",
        readonly=True,
        states={"draft": [("readonly", False)]},
        tracking=True,
    )
    contract_id = fields.Many2one(
        "hr.contract",
        string="Contract",
        readonly=True,
        tracking=True,
        states={"draft": [("readonly", False)]},
    )
    details_by_salary_rule_category = fields.One2many(
        "hr.payslip.line",
        compute="_compute_details_by_salary_rule_category",
        string="Details by Salary Rule Category",
    )
    dynamic_filtered_payslip_lines = fields.One2many(
        "hr.payslip.line",
        compute="_compute_dynamic_filtered_payslip_lines",
        string="Dynamic Filtered Payslip Lines",
    )
    credit_note = fields.Boolean(
        string="Credit Note",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Indicates this payslip has a refund of another",
    )
    payslip_run_id = fields.Many2one(
        "hr.payslip.run",
        string="Payslip Batches",
        readonly=True,
        copy=False,
        tracking=True,
        states={"draft": [("readonly", False)]},
    )
    payslip_count = fields.Integer(
        compute="_compute_payslip_count", string="Payslip Computation Details"
    )
    hide_child_lines = fields.Boolean(string="Hide Child Lines", default=False)

    @api.depends("line_ids", "hide_child_lines")
    def _compute_dynamic_filtered_payslip_lines(self):
        for payslip in self:
            if payslip.hide_child_lines:
                payslip.dynamic_filtered_payslip_lines = payslip.mapped(
                    "line_ids"
                ).filtered(lambda line: not line.parent_rule_id)
            else:
                payslip.dynamic_filtered_payslip_lines = payslip.line_ids

    @api.depends("line_ids")
    def _compute_details_by_salary_rule_category(self):
        for payslip in self:
            payslip.details_by_salary_rule_category = payslip.mapped(
                "line_ids"
            ).filtered(lambda line: line.category_id and line.appears_on_payslip)

    def _compute_payslip_count(self):
        for payslip in self:
            payslip.payslip_count = len(payslip.line_ids)

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        if any(self.filtered(lambda payslip: payslip.date_from > payslip.date_to)):
            raise ValidationError(
                _("Payslip 'Date From' must be earlier than 'Date To'.")
            )

    def copy(self, default=None):
        rec = super().copy(default)
        for line in self.input_line_ids:
            line.copy({"payslip_id": rec.id})
        for line in self.line_ids:
            line.copy({"slip_id": rec.id, "input_ids": []})
        return rec

    def action_payslip_draft(self):
        return self.write({"state": "draft"})

    def action_payslip_done(self):
        if not self.env.context.get("without_compute_sheet"):
            self.compute_sheet()
        return self.write({"state": "done"})

    def action_payslip_cancel(self):
        if self.filtered(lambda slip: slip.state == "done"):
            raise UserError(_("Cannot cancel a payslip that is done."))
        return self.write({"state": "cancel"})

    def refund_sheet(self):
        for payslip in self:
            copied_payslip = payslip.copy(
                {"credit_note": True, "name": _("Refund: %s") % payslip.name}
            )
            number = copied_payslip.number or self.env["ir.sequence"].next_by_code(
                "salary.slip"
            )
            copied_payslip.write({"number": number})
            copied_payslip.with_context(
                without_compute_sheet=True
            ).action_payslip_done()
        formview_ref = self.env.ref("payroll.hr_payslip_view_form", False)
        treeview_ref = self.env.ref("payroll.hr_payslip_view_tree", False)
        return {
            "name": _("Refund Payslip"),
            "view_mode": "tree, form",
            "view_id": False,
            "res_model": "hr.payslip",
            "type": "ir.actions.act_window",
            "target": "current",
            "domain": "[('id', 'in', %s)]" % copied_payslip.ids,
            "views": [
                (treeview_ref and treeview_ref.id or False, "tree"),
                (formview_ref and formview_ref.id or False, "form"),
            ],
            "context": {},
        }

    def check_done(self):
        return True

    def unlink(self):
        if any(self.filtered(lambda payslip: payslip.state not in ("draft", "cancel"))):
            raise UserError(
                _("You cannot delete a payslip which is not draft or cancelled")
            )
        return super(HrPayslip, self).unlink()

    def compute_sheet(self):
        for payslip in self:
            number = payslip.number or self.env["ir.sequence"].next_by_code(
                "salary.slip"
            )
            # delete old payslip lines
            payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be
            # for all current contracts of the employee
            contract_ids = (
                payslip.contract_id.ids
                or payslip.employee_id._get_contracts(
                    date_from=payslip.date_from, date_to=payslip.date_to
                ).ids
            )
            lines = [
                (0, 0, line)
                for line in self._get_payslip_lines(contract_ids, payslip.id)
            ]
            payslip.write({"line_ids": lines, "number": number})
        return True

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contracts: Browse record of contracts
        @return: returns a list of dict containing the input that should be
        applied for the given contract between date_from and date_to
        """
        res = []
        for contract in contracts.filtered(
            lambda contract: contract.resource_calendar_id
        ):
            day_from = datetime.combine(date_from, time.min)
            day_to = datetime.combine(date_to, time.max)
            day_contract_start = datetime.combine(contract.date_start, time.min)
            # Support for the hr_public_holidays module.
            contract = contract.with_context(
                employee_id=self.employee_id.id, exclude_public_holidays=True
            )
            # only use payslip day_from if it's greather than contract start date
            if day_from < day_contract_start:
                day_from = day_contract_start
            # == compute leave days == #
            leaves = self._compute_leave_days(contract, day_from, day_to)
            res.extend(leaves)
            # == compute worked days == #
            attendances = self._compute_worked_days(contract, day_from, day_to)
            res.append(attendances)
        return res

    def _compute_leave_days(self, contract, day_from, day_to):
        """
        Leave days computation
        @return: returns a list containing the leave inputs for the period
        of the payslip. One record per leave type.
        """
        leaves_positive = (
            self.env["ir.config_parameter"].sudo().get_param("payroll.leaves_positive")
        )
        leaves = {}
        calendar = contract.resource_calendar_id
        tz = timezone(calendar.tz)
        day_leave_intervals = contract.employee_id.list_leaves(
            day_from, day_to, calendar=contract.resource_calendar_id
        )
        for day, hours, leave in day_leave_intervals:
            holiday = leave[:1].holiday_id
            current_leave_struct = leaves.setdefault(
                holiday.holiday_status_id,
                {
                    "name": holiday.holiday_status_id.name or _("Global Leaves"),
                    "sequence": 5,
                    "code": holiday.holiday_status_id.code or "GLOBAL",
                    "number_of_days": 0.0,
                    "number_of_hours": 0.0,
                    "contract_id": contract.id,
                },
            )
            if leaves_positive:
                current_leave_struct["number_of_hours"] += hours
            else:
                current_leave_struct["number_of_hours"] -= hours
            work_hours = calendar.get_work_hours_count(
                tz.localize(datetime.combine(day, time.min)),
                tz.localize(datetime.combine(day, time.max)),
                compute_leaves=False,
            )
            if work_hours:
                if leaves_positive:
                    current_leave_struct["number_of_days"] += hours / work_hours
                else:
                    current_leave_struct["number_of_days"] -= hours / work_hours
        return leaves.values()

    def _compute_worked_days(self, contract, day_from, day_to):
        """
        Worked days computation
        @return: returns a list containing the total worked_days for the period
        of the payslip. This returns the FULL work days expected for the resource
        calendar selected for the employee (it don't substract leaves by default).
        """
        work_data = contract.employee_id._get_work_days_data(
            day_from,
            day_to,
            calendar=contract.resource_calendar_id,
            compute_leaves=False,
        )
        return {
            "name": _("Normal Working Days paid at 100%"),
            "sequence": 1,
            "code": "WORK100",
            "number_of_days": work_data["days"],
            "number_of_hours": work_data["hours"],
            "contract_id": contract.id,
        }

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        # TODO: We leave date_from and date_to params here for backwards
        # compatibility reasons for the ones who inherit this function
        # in another modules, but they are not used.
        # Will be removed in next versions.
        """
        Inputs computation.
        @returns: Returns a dict with the inputs that are fetched from the salary_structure
        associated rules for the given contracts.
        """
        res = []
        current_structure = self.struct_id
        structure_ids = contracts.get_all_structures()
        if current_structure:
            structure_ids = list(set(current_structure._get_parent_structure().ids))
        rule_ids = (
            self.env["hr.payroll.structure"].browse(structure_ids).get_all_rules()
        )
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        payslip_inputs = (
            self.env["hr.salary.rule"].browse(sorted_rule_ids).mapped("input_ids")
        )
        for contract in contracts:
            for payslip_input in payslip_inputs:
                res.append(
                    {
                        "name": payslip_input.name,
                        "code": payslip_input.code,
                        "contract_id": contract.id,
                    }
                )
        return res

    def _init_payroll_dict_contracts(self):
        return {
            "count": 0,
        }

    def get_payroll_dict(self, contracts):
        """Setup miscellaneous dictionary values.
        Other modules may overload this method to inject discreet values into
        the salary rules. Such values will be available to the salary rule
        under the `payroll.` prefix.

        This method is evaluated once per payslip.
        :param contracts: Recordset of all hr.contract records in this payslip
        :return: a dictionary of discreet values and/or Browsable Objects
        """
        self.ensure_one()

        res = {
            # In salary rules refer to this as: payroll.contracts.count
            "contracts": BaseBrowsableObject(self._init_payroll_dict_contracts()),
        }
        res["contracts"].count = len(contracts)

        return res

    def get_baselocaldict(self, contracts):
        """Basic dictionary values that are useful in most salary rules. Inherited
        classes that overload this method should use the name of the module as
        the dictionary key.

        This method is evaluated once per payslip.

        :param contracts: Recordset of all hr.contract records in this payslip
        :return: a dictionary of discreet values and/or Browsable Objects
        """
        self.ensure_one()

        worked_days_dict = {}
        inputs_dict = {}
        payslip = self
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        payroll_dict = BrowsableObject(
            payslip.employee_id.id, payslip.get_payroll_dict(contracts), self.env
        )

        baselocaldict = {
            "payslip": payslips,
            "worked_days": worked_days,
            "inputs": inputs,
            "payroll": payroll_dict,
        }
        return baselocaldict

    def get_contract_dict(self, contract, contracts):
        """Contract dependent dictionary values.
        This method is called just before the salary rules are evaluated for
        contract.

        This method is evaluated once for every contract in the payslip.

        :param contract: The current hr.contract being processed
        :param contracts: Recordset of all hr.contract records in this payslip
        :return: a dictionary of discreet values and/or Browsable Objects
        """
        self.ensure_one()

        # res = super().get_contract_dict(contract, contracts)
        # res.update({
        #     # In salary rules refer to these as:
        #     #     current_contract.foo
        #     #     current_contract.foo.bar.baz
        #     "foo": 0,
        #     "bar": BaseBrowsableObject(
        #         {
        #             "baz": 0
        #         }
        #     )
        # })
        # <do something to update values in res>
        # return res

        return {}

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(
                    localdict, category.parent_id, amount
                )

            if category.code in localdict["categories"].dict:
                localdict["categories"].dict[category.code] += amount
            else:
                localdict["categories"].dict[category.code] = amount

            return localdict

        payslip = self.env["hr.payslip"].browse(payslip_id)
        contracts = self.env["hr.contract"].browse(contract_ids)

        # we keep a dict with the result because a value can be overwritten by
        # another rule with the same code
        result_dict = {}
        rules_dict = {}
        contract_dict = {}
        blacklist = []
        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)
        current_contract = BrowsableObject(
            payslip.employee_id.id, contract_dict, self.env
        )

        baselocaldict = payslip.get_baselocaldict(contracts)
        baselocaldict["categories"] = categories
        baselocaldict["rules"] = rules
        baselocaldict["current_contract"] = current_contract

        # get the ids of the structures on the contracts and their parent id
        # as well
        if len(contracts) == 1 and payslip.struct_id:
            structure_ids = list(set(payslip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = (
            self.env["hr.payroll.structure"].browse(structure_ids).get_all_rules()
        )
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env["hr.salary.rule"].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            contract_dict = payslip.get_contract_dict(contract, contracts)
            baselocaldict["current_contract"] = BrowsableObject(
                payslip.employee_id.id, contract_dict, self.env
            )
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in sorted_rules:
                key = rule.code + "-" + str(contract.id)
                localdict["result"] = None
                localdict["result_qty"] = 1.0
                localdict["result_rate"] = 100
                localdict["result_name"] = None
                # check if the rule can be applied
                if rule._satisfy_condition(localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate, computed_name = rule._compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = (
                        rule.code in localdict and localdict[rule.code] or 0.0
                    )
                    # set/overwrite the amount computed for this rule in the
                    # localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(
                        localdict, rule.category_id, tot_rule - previous_amount
                    )
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        "salary_rule_id": rule.id,
                        "contract_id": contract.id,
                        "name": computed_name and str(computed_name) or rule.name,
                        "code": rule.code,
                        "category_id": rule.category_id.id,
                        "sequence": rule.sequence,
                        "appears_on_payslip": rule.appears_on_payslip,
                        "parent_rule_id": rule.parent_rule_id.id,
                        "condition_select": rule.condition_select,
                        "condition_python": rule.condition_python,
                        "condition_range": rule.condition_range,
                        "condition_range_min": rule.condition_range_min,
                        "condition_range_max": rule.condition_range_max,
                        "amount_select": rule.amount_select,
                        "amount_fix": rule.amount_fix,
                        "amount_python_compute": rule.amount_python_compute,
                        "amount_percentage": rule.amount_percentage,
                        "amount_percentage_base": rule.amount_percentage_base,
                        "register_id": rule.register_id.id,
                        "amount": amount,
                        "employee_id": contract.employee_id.id,
                        "quantity": qty,
                        "rate": rate,
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in rule._recursive_search_of_rules()]
            baselocaldict["current_contract"] = {}

        return list(result_dict.values())

    def get_payslip_vals(
        self, date_from, date_to, employee_id=False, contract_id=False, struct_id=False
    ):
        # Initial default values for generated payslips
        employee = self.env["hr.employee"].browse(employee_id)
        res = {
            "value": {
                "line_ids": [],
                "input_line_ids": [(2, x) for x in self.input_line_ids.ids],
                "worked_days_line_ids": [(2, x) for x in self.worked_days_line_ids.ids],
                "name": "",
                "contract_id": False,
                "struct_id": False,
            }
        }

        # If we don't have employee or date data, we return.
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        # We check if contract_id is present, if not we fill with the
        # first contract of the employee. If not contract present, we return.
        if not self.env.context.get("contract"):
            contract_ids = employee.contract_id.ids
        else:
            if contract_id:
                contract_ids = [contract_id]
            else:
                contract_ids = employee._get_contracts(
                    date_from=date_from, date_to=date_to
                ).ids
        if not contract_ids:
            return res
        contract = self.env["hr.contract"].browse(contract_ids[0])
        res["value"].update({"contract_id": contract.id})
        # We check if struct_id is already filled, otherwise we assign the contract struct.
        # If contract don't have a struct, we return.
        if struct_id:
            res["value"].update({"struct_id": struct_id[0]})
        else:
            struct = contract.struct_id
            if not struct:
                return res
            res["value"].update({"struct_id": struct.id})
        # Computation of the salary input and worked_day_lines
        contracts = self.env["hr.contract"].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        res["value"].update(
            {
                "worked_days_line_ids": worked_days_line_ids,
                "input_line_ids": input_line_ids,
            }
        )
        return res

    def _get_employee_contracts(self):
        return self.env["hr.contract"].browse(
            self.employee_id._get_contracts(
                date_from=self.date_from, date_to=self.date_to
            ).ids
        )

    @api.onchange("struct_id")
    def onchange_struct_id(self):
        if not self.struct_id:
            self.input_line_ids.unlink()
            return
        input_lines = self.input_line_ids.browse([])
        input_line_ids = self.get_inputs(
            self._get_employee_contracts(), self.date_from, self.date_to
        )
        for r in input_line_ids:
            input_lines += input_lines.new(r)
        self.input_line_ids = input_lines

    @api.onchange("date_from", "date_to")
    def onchange_dates(self):
        if not self.date_from or not self.date_to:
            return
        worked_days_lines = self.worked_days_line_ids.browse([])
        worked_days_line_ids = self.get_worked_day_lines(
            self._get_employee_contracts(), self.date_from, self.date_to
        )
        for line in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(line)
        self.worked_days_line_ids = worked_days_lines

    @api.onchange("employee_id", "date_from", "date_to")
    def onchange_employee(self):
        # Return if required values are not present.
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        # Assign contract_id automatically when the user don't selected one.
        if not self.env.context.get("contract") or not self.contract_id:
            contract_ids = self._get_employee_contracts().ids
            if not contract_ids:
                return
            self.contract_id = self.env["hr.contract"].browse(contract_ids[0])
        # Assign struct_id automatically when the user don't selected one.
        if not self.struct_id and not self.env.context.get("struct_id"):
            if not self.contract_id.struct_id:
                return
            self.struct_id = self.contract_id.struct_id
        # Compute payslip name
        self._compute_name()
        # Call worked_days_lines computation when employee is changed.
        self.onchange_dates()
        # Call input_lines computation when employee is changed.
        self.onchange_struct_id()
        # Assign company_id automatically based on employee selected.
        self.company_id = self.employee_id.company_id

    def _compute_name(self):
        for record in self:
            record.name = _("Salary Slip of %s for %s") % (
                record.employee_id.name,
                tools.ustr(
                    babel.dates.format_date(
                        date=datetime.combine(record.date_from, time.min),
                        format="MMMM-y",
                        locale=record.env.context.get("lang") or "en_US",
                    )
                ),
            )

    @api.onchange("contract_id")
    def onchange_contract(self):
        if not self.contract_id:
            self.struct_id = False
        self.with_context(contract=True).onchange_employee()
        return

    def get_salary_line_total(self, code):
        self.ensure_one()
        line = self.line_ids.filtered(lambda line: line.code == code)
        if line:
            return line[0].total
        else:
            return 0.0
