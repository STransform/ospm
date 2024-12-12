from odoo import api, models, fields
from odoo.exceptions import ValidationError


class HrOvertimePaymentItem(models.Model):
    _name = "hr.overtime.payment.item"
    _description = "Overtime Payment Item"
    _order = "create_date desc"
    _rec_name = "display_name"

    overtime_payment_id = fields.Many2one(
        "hr.overtime.payment", string="Overtime Payment", ondelete="cascade"
    )

    start_date = fields.Date(
        string="Start Date",
        required=True,
        tracking=True,
    )
    end_date = fields.Date(
        string="End Date",
        required=True,
        tracking=True,
    )
    hours = fields.Float(
        string="Hours",
        required=True,
        tracking=True,
    )

    overtime_rate_id = fields.Many2one(
        "hr.overtime.rate",
        string="Overtime Rate type",
        required=True,
        tracking=True,
    )

    amount = fields.Float(
        string="Amount",
        compute="_compute_amount",
        store=True,
        tracking=True,
    )

    @api.depends("hours", "overtime_rate_id")
    def _compute_amount(self):
        for record in self:
            contract = record.overtime_payment_id.employee_id.contract_id
            if contract and contract.state == "open":
                wage = contract.wage
                salary_per_hour = wage / 240
                rate = record.overtime_rate_id
                if record.hours > 0:
                    record.amount = (
                        salary_per_hour * (rate.hourly_rate / 100) * record.hours
                    )
                else:
                    record.amount = 0.0

    @api.constrains("hours")
    def _validate_hours(self):
        for record in self:
            if record.hours <= 0:
                raise ValidationError("Worked Hours Must be positive number!")

    @api.constrains("start_date", "end_date")
    def _validate_date(self):
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError("Start date cannot exceed than End date!")
