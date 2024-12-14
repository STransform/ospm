"""
This module manages retirement extension requests for employees.
It handles the creation, submission, approval, and rejection of requests to 
extend an employee's retirement date.
The module includes functionality for notifications and validation of extension periods.
"""
from odoo import models, fields, api,_
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from datetime import date


class HrRetirementExtensionRequest(models.Model):
    """
        Model for managing retirement extension requests.
        Inherits:
        - mail.thread
        - mail.activity.mixin
    """
    _name = 'hr.retirement.extension.request'
    _description = 'Retirement Extension Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    employee_department = fields.Char(string="Department", compute='_compute_employee_information', readonly=True)
    user_id = fields.Many2one('res.users', string="Requested By", readonly=True)
    extension_reason = fields.Text(string="Extension Reason", required=True)
    extension_period_months = fields.Integer(string="Extension Period (Months)", required=True)
    current_retirement_date = fields.Date(string="Current Retirement Date", required=True, compute='_compute_employee_information')
    proposed_new_retirement_date = fields.Date(string="Proposed New Retirement Date", compute="_compute_new_retirement_date", store=True)
    request_date = fields.Date(string="Request Submission Date", default=fields.Date.today, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Status", default='draft', readonly=True)
    
    employee_state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Employee Status", default='pending', readonly=True)

    comment = fields.Text(string="Comment")
    user_can_comment = fields.Boolean(string="Can Comment", compute="_compute_user_can_comment", store=False)

    
    @api.model
    def send_notification(self, message, user, title):
        """
            Send a notification to a specific user.
            
            Args:
                message: The notification message
                user: The user to receive the notification
                title: The title of the notification
        """ 
        self.env['custom.notification'].create({
            'title': title,
            'message': message,
            'user_id': user.id,
        })

    @api.depends('employee_id')
    def _compute_employee_information(self):
        """
            Compute employee related information including department and retirement date.
            Validates if employee is eligible for retirement extension.
        """
        for record in self:
            if not record._origin and record.employee_id and not self.employee_id.near_retirement:
                raise ValidationError(_("The Employee is not allowed for the Extending the retirment period."))
            if record.employee_id:
                if not record.employee_id.user_id:
                    raise ValidationError(_("The Employee Doesn't Have a related User Account. Please Add User Account for the Employee"))
                if not record.employee_id.department_id:
                    raise ValidationError(_("The Employee Doesn't Have a Department. Please Add Department for the Employee"))
                record.employee_department = record.employee_id.department_id.name
                record.current_retirement_date = record.employee_id.retirement_date
                record.user_id = record.employee_id.user_id.id
            else:
                record.employee_department = False
                record.current_retirement_date = False


    @api.depends('extension_period_months')
    def _compute_new_retirement_date(self):
        """
            Compute the new proposed retirement date based on extension period.
            
            Updates proposed_new_retirement_date field by adding extension_period_months 
            to current retirement date.
        """
        for record in self:
            if record.current_retirement_date and record.extension_period_months:
                record.proposed_new_retirement_date = fields.Date.from_string(record.current_retirement_date) + relativedelta(months=record.extension_period_months)

    @api.model
    def _compute_user_can_comment(self):
        """
            Determine if current user has permission to comment on the request.
            Sets user_can_comment based on whether user is the employee making the request.
        """
        for record in self:
            record.user_can_comment = self.env.user.id == record.employee_id.user_id.id
    

    @api.constrains('extension_period_months')
    def _check_extension_period(self):
        """
            Validate extension period constraints.
            Raises ValidationError if period is not positive.
        """
        """Ensure the extension period is valid."""
        if not self._origin and self.extension_period_months <= 0:
            raise ValidationError("The extension period must be greater than 0 months.")
    


    def action_submit(self):
        """
            Submit the extension request for approval.
            Updates state, sends notifications to relevant users.
            
            Raises:
                ValidationError: If request is not in draft state
        """
        """Submit the extension request."""
        if self.state != 'draft':
            raise ValidationError("Only draft requests can be submitted.")
        self.state = 'submitted'
        self.request_date = fields.Date.today()
        self.employee_state = 'pending'

        ## send notification to the employee
        message = f"The Hr Office has requested you for Extending your retirment period for {self.extension_period_months} months"
        self.send_notification(message=message, user=self.employee_id.user_id, title=self._description)
        self.employee_id.user_id.notify_info(message=message, title=self._description)
        self.env.user.notify_success(message="Retirement Extension Request Submitted Successfully.", title=self._description)



    def action_approve(self):
        """
            Approve the extension request.
            Updates employee retirement date and sends notifications.
            Calculates if employee is near retirement based on new date.
        """
        """Approve the extension request and update the employee's retirement date."""
        retirement_threshold = self.env['hr.retirement.settings'].sudo().search([], limit=1).retirement_threshold_months
        near_retirement = date.today() >= self.proposed_new_retirement_date - relativedelta(months=retirement_threshold)
        self.state = 'approved'
        self.employee_state = 'approved'
        self.sudo().employee_id.write({
            'retirement_extended': True,
            'retirement_date': self.proposed_new_retirement_date,
            'near_retirement' : near_retirement
        })

        ## send notification to the employee
        message = f"{self.employee_id.name} has Accepted the request for extending the Retirment Request"
        self.send_notification(message=message, user=self.create_uid, title=self._description)
        self.create_uid.notify_success(message=message, title=self._description)
        self.env.user.notify_success(message="Retirement Extension Request Accepted Successfully.", title=self._description)


    def action_reject(self):
        """
            Reject the extension request.
            Updates request state and sends notifications to relevant users.
        """
        """Reject the extension request."""
        self.state = 'rejected'
        self.employee_state = 'rejected'

        ## send notification to the employee
        message = f"{self.employee_id.name} has Rejected the request for extending the Retirment Request"
        self.send_notification(message=message, user=self.create_uid, title=self._description)
        self.create_uid.notify_warning(message=message, title=self._description)
        self.env.user.notify_warning(message="Retirement Extension Request Rejected Successfully.", title=self._description)



