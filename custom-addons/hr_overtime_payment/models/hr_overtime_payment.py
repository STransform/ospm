from odoo import models, fields, api
from datetime import datetime
from babel.dates import format_date


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
    

    # Format the date to a human-readable format
    def _format_date(self, date):
        if date:
            return format_date(date, format="long", locale=self.env.user.lang or "en_US")
        return ""

     # add notification function 
    @api.model
    def send_notification(self, message, user, title):
        self.env['custom.notification'].create({
            'title': title,
            'message': message,
            'user_id': user.id,
        })



    @api.depends("employee_id")
    def _compute_wage(self):
        for record in self:
            if record.employee_id.contract_id.wage:
                record.wage = record.employee_id.contract_id.wage
            else:
                record.wage = 0.0

    
    # clear list onchange eployee
    @api.onchange("employee_id")
    def _clear_payment_items(self):
        for record in self:
            record.overtime_payment_item_ids = None
    # total amount calculation
    @api.depends("overtime_payment_item_ids.amount")
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(
                item.amount for item in record.overtime_payment_item_ids
            )
            
    def action_submit(self):
        # notification
        ## search users with specific group
        hr_office = self.env.ref("user_group.group_hr_office").users
        title = "New Request for Overtime Payment"
        message = f"New Request to be approved."
        for user in hr_office:
            self.send_notification(message, user, title) 
            user.notify_success(title=title, message=message)
        self.env.user.notify_success("Request Submitted")
        
        self.state = "submitted"

    def action_approve(self):
        # store  Overtime Payment history
        self.env["hr.overtime.payment.history"].create(
            {
                "reference": self.id,
                "employee_id": self.employee_id.id,
                "overtime_approved_date": fields.Datetime.now(),
                "approved_by": self.env.user.id,
                "overtime_amount": self.total_amount,
            }
        )
        self.state = "approved"
        ## search users with specific group
        department_manager = self.env.ref("user_group.group_department_manager").users
        title = "Overtime Payment Approved"
        message = f"approved."
        for user in department_manager:
            self.send_notification(message, user, title) 
            user.notify_success(title=title, message=message)
        self.env.user.notify_success("Request Successfully Approved")

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
        
