"""
This module handles employee retirement requests in Odoo.
It manages the submission, approval, and rejection of retirement requests,
as well as the automatic deactivation of retired employees.
"""
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
from babel.dates import format_date
class HrRetirementRequest(models.Model):
    """
    Model for managing employee retirement requests.
    Inherits:
        - mail.thread
        - mail.activity.mixin
    """
    _name = 'hr.retirement.request'
    _description = 'Retirement Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env.user.employee_id, readonly=True)
    department = fields.Char(string="Department", related='employee_id.department_id.name', readonly=True)
    proposed_retirement_date = fields.Date(string="Proposed Retirement Date", default = lambda self: self.env.user.employee_id.retirement_date, readonly=True)
    request_date = fields.Date(string="Request Submission Date", default=fields.Date.today(), readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Status", default='draft', readonly=True)

    ceo_state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="CEO Status", default='pending', readonly=True)


    comment = fields.Text(string="Comment")
    user_can_comment = fields.Boolean(string="Can Comment", compute="_compute_user_can_comment", store=False)


    def _format_date(self, date):
        """
        Format a date to a human-readable string.
        
        Args:
            date (datetime.date): The date to format
            
        Returns:
            str: Formatted date string in the user's locale
        """
        if date:
            return format_date(date, format="long", locale=self.env.user.lang or "en_US")
        return ""

    @api.model
    def send_notification(self, message, user, title,model,res_id):
        """
        Send a notification to a specific user.
        
        Args:
            message (str): The notification message
            user (res.users): The user to notify
            title (str): The notification title
            model (str): The model name
            res_id (int): The record ID
        """
        self.env['custom.notification'].create({
            'title': title,
            'message': message,
            'user_id': user.id,
            'action_model':model,
            'action_res_id': res_id
        })

    @api.model
    def _compute_user_can_comment(self):
        """
        Compute if current user has permission to comment.
        Sets user_can_comment based on CEO group membership.
        """
        for record in self:
            record.user_can_comment = self.env.user.has_group("user_group.group_ceo")

    @api.onchange('employee_id')
    def is_valid_employee(self):
        """
        Validate if selected employee is eligible for retirement.
        Raises ValidationError if employee is not near retirement.
        """
        if not self.employee_id.near_retirement:
            raise ValidationError("You are not Allowed To Request for retirement. Please consider requesting for Early retirement")

    
    def action_submit(self):
        """
        Submit the retirement request.
        Updates state and sends notifications to CEO users.
        """
        self.state = 'submitted'
        self.request_date = datetime.today()

        ceo = self.env.ref('user_group.group_ceo').users
        message = f"{self.employee_id.name} has submitted a retirement request, proposing to retire on {self._format_date(self.proposed_retirement_date)}"
        for user in ceo:
            self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
            user.notify_success(message=message, title=self._description)
        self.env.user.notify_success(message="Retirement Request Submitted Successfully.", title=self._description)

    def action_approve(self):
        """
        Approve the retirement request.
        Updates state and sends approval notification to employee.
        """
        self.state = 'approved'
        self.ceo_state = 'approved'

        message = f"Your Retirement Request has been approved."
        self.send_notification(message=message, user=self.employee_id.user_id, title=self._description, model=self._name, res_id=self.id)
        self.employee_id.user_id.notify_success(message=message, title=self._description)
        self.env.user.notify_success(message="Retirement Request Approved Successfully.", title=self._description)

    def action_reject(self):
        """
        Reject the retirement request.
        Updates state and sends rejection notification to employee.
        """
        self.state = 'rejected'
        self.ceo_state = 'rejected'

        message = f"Your Retirement Request has been rejected."
        self.send_notification(message=message, user=self.employee_id.user_id, title=self._description, model=self._name, res_id=self.id)
        self.employee_id.user_id.notify_warning(message=message, title=self._description)
        self.env.user.notify_warning(message="Retirement Request Rejected.", title=self._description)
    

    def update_retired_employee(self):
        """
        Update all retirement requests.
        Calls retire_employee() on all records.
        """
        employees = self.search([])
        employees.retire_employee()  

    def retire_employee(self):
        """
        Process retirement for approved employees.
        Deactivates employee and user accounts if retirement date has passed.
        """
        for record in self:
            if record.state == 'approved' and record.employee_id.retirement_date and record.employee_id.retirement_date <= datetime.now().date():
                record.employee_id.near_retirement = False
                record.employee_id.is_retired = True
                if record.employee_id.user_id:
                    record.employee_id.user_id.active = False 
                record.employee_id.active = False
