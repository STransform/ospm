from odoo import models, fields, api
from datetime import datetime


class HrOvertimePayment(models.Model):
    _name = "hr.overtime.payment"
    _description = "Overtime Payment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"
    _rec_name= "employee_id"

    overtime_payment_item_ids = fields.One2many(
        "hr.overtime.payment.item",
        "overtime_payment_id",
        string="Overtime Payment Items",
        required=True,
        tracking=True,
    )
    employee_id = fields.Many2one(
        "hr.employee", string="Employee", tracking=True, required=True
    )
    department_id = fields.Many2one(
        "hr.department", string="Department", related="employee_id.department_id"
    )
    approved_date = fields.Date(
        string="Approved Date",
        tracking=True,
    )
    rejection_reason = fields.Text(string="Rejection Reason")
    contract_id = fields.Many2one(
        "hr.contract", string="Contract", related="employee_id.contract_id"
    )
    currency_id = fields.Many2one("res.currency", related="contract_id.currency_id")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    total_amount = fields.Float(
        string="Total Amount",
        compute="_compute_amount",
        store=True,
        tracking=True,
    )

    # @api.depends("employee_id", "hours", "overtime_rate_id")
    # def _compute_amount(self):
    #     for record in self:
    #         contract = record.employee_id.contract_id
    #         if contract and contract.state == "open":
    #             wage = contract.wage
    #             salary_per_hour = wage / 240
    #             rate = record.overtime_rate_id
    #             if record.hours > 0:
    #                 record.amount = salary_per_hour * (rate.hourly_rate/100) * record.hours
    #             else:
    #                 record.amount = 0.0

    def action_submit(self):
        self.state = "submitted"

    def action_approve(self):
        # store  bonus history
        # self.env["hr.bonus.history"].create(
        #     {
        #         "reference": self.id,
        #         "employee_id": line.employee_id.id,
        #         "bonus_approved_date": fields.Datetime.now(),
        #         "approved_by": self.env.user.id,
        #         "bonus_amount": line.bonus_amount,
        #     }
        # )
        self.state = "approved"

    def action_reject(self):
        """Reject the batch."""
        return {
            "name": "Reject Overtime Request",
            "type": "ir.actions.act_window",
            "res_model": "hr.overtime.payment.rejection.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_rejection_reason": self.rejection_reason},
        }