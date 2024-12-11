from odoo import models, fields, api
from datetime import datetime


class HrOvertimePayment(models.Model):
    _name = "hr.overtime.payment"
    _description = "Overtime Payment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"
    _rec_name = "employee_id"

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
    wage = fields.Float(
        string="Wage per Month", compute="_compute_wage", tracking=True, required=True
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
        compute="_compute_total_amount",
        store=True,
        tracking=True,
    )

    @api.depends("employee_id")
    def _compute_wage(self):
        for record in self:
            if record.employee_id.contract_id.wage:
                record.wage = record.employee_id.contract_id.wage
            else:
                record.wage = 0.0

    # total amount calculation
    @api.depends("overtime_payment_item_ids.amount")
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(
                item.amount for item in record.overtime_payment_item_ids
            )

    def action_submit(self):
        self.state = "submitted"

    def action_approve(self):
        # store  Overtime Payment history
        self.env["hr.overtime.payment.history"].create(
            {
                "reference": self.id,
                "employee_id": self.employee_id,
                "overtime_approved_date": fields.Datetime.now(),
                "approved_by": self.env.user.id,
                "overtime_amount": self.total_amount,
            }
        )
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
