from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrAnalyticQtyRateAmount(models.Model):
    _name = "hr.payslip.line.manually"
    _description = "hr.payslip.line.manually"

    @api.model
    def _compute_default_model(self):
        try:
            return self.env.context["params"]["model"]
        except:
            raise UserError(
                _(
                    """Please save changes, then refresh the page (F5).
                    If needed, use the menu Payroll / Employee Payslips,
                    or the menu Employees / Employees / Contracts."""
                )
            )

    salary_rule_id = fields.Many2one(
        "hr.salary.rule", string="Salary Rule", ondelete="restrict"
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Analytic Account", ondelete="restrict"
    )
    quantity = fields.Float(default=1.0)
    rate = fields.Float("Rate (%)", default=100.0)
    amount = fields.Float()
    total = fields.Float(compute="_compute_total")
    model = fields.Char(
        required=True, readonly=True, index=True, default=_compute_default_model
    )
    res_id = fields.Integer(
        required=True,
        readonly=True,
        index=True,
        ondelete="""Should NOT be "cascade", see the write method""",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        store=True,
        index=True,
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        (
            "rule_analytic_uniq",
            "UNIQUE(salary_rule_id, analytic_account_id, res_id)",
            "The combination of salary rule and analytic account must be unique!",
        ),
    ]

    def _valid_field_parameter(self, field, name):
        return name == "ondelete" or super()._valid_field_parameter(field, name)

    @api.depends("quantity", "rate", "amount")
    def _compute_total(self):
        for rec in self:
            rec.total = rec.quantity * rec.rate / 100 * rec.amount

    def write(self, values):
        """
        SOURCE: base_field_value
        Payslip/Contract:analytic_qty_rate_amount_ids = \
            fields.One2many("hr.analytic.qty.rate.amount", "res_id"):
        The model assumes that hr.analytic.qty.rate.amount "res_id"
        has a Many2one relationship to the model.
        When the model imports a new record (with csv/xml),
        it will enforce that the new record.id does not exist
        in hr.analytic.qty.rate.amount "res_id",
        or give a ParseError if "res_id" has no attribute "ondelete".
        See https://github.com/odoo/odoo/blob/10.0/odoo/fields.py#L2246
                    if inverse_field.ondelete == "cascade":
                        comodel.search(domain).unlink()
                    else:
                        comodel.search(domain).write({inverse: False})
        hr.analytic.qty.rate.amount has records relating to multiple models,
        and the "res_id" should not be changed!
        """
        if "res_id" in values and values["res_id"] == False:
            values.pop("res_id")
        return super(HrAnalyticQtyRateAmount, self).write(values)

    def get_result_dict(
        self, months=1.0, multiply_with=None, uom=None, default_amount=0.0
    ):
        """
        Method to use in hr.salary.rule python code.

        :param months (float): how many months (assuming monthly contract)
        :param multiply_with (string): which field to multiply,
            should be "result_qty" or "result_rate"
        :param uom (string): unit of measure to include in the name of the payslip line
        :param default_amount: the amount to use if record.amount is 0
        :return: dictionary of values for payslip line

        If months is not 1.00:
            Set the "months" and what to "multiply_with" ("result_qty" or "result_rate").
            If "uom" is set, the payslip line will include this text.
        If record.amount is 0, use "default_amount".
        """
        record = self.ensure_one()
        result_dict = {
            "result_name": record.salary_rule_id.name,
            "result_analytic": record.analytic_account_id.id,
            "result_qty": record.quantity,
            "result_rate": record.rate,
            "result": record.amount,
        }
        if round(months, 2) != 1.00:
            if uom:
                uom = " á {:.2f} {}".format(result_dict[multiply_with], uom)
            result_dict["result_name"] += " ({:.2f} months{})".format(months, uom)
            result_dict[multiply_with] *= months
        if not result_dict["result"]:
            result_dict["result"] = default_amount
        return result_dict
