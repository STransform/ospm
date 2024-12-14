from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from babel.dates import format_date

class EarlyRetirementRequest(models.Model):
    """
    Early Retirement Request Model

    This model manages early retirement requests for employees, including submission,
    approval/rejection workflow, and employee deactivation upon retirement.

    Inherits:
        - mail.thread
        - mail.activity.mixin
    """
    _name = 'hr.early.retirement.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Early Retirement Request'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env.user.employee_id, readonly=True)
    employee_name = fields.Char(string="Employee", related='employee_id.name', readonly=True)
    department = fields.Char(string="Department", related='employee_id.department_id.name', readonly=True)
    proposed_retirement_date = fields.Date(string="Proposed Retirement Date", required=True)
    request_date = fields.Date(string="Request Submission Date", default=fields.Date.today, readonly=True)
    reason = fields.Text(string="Reason", required=True, help="Provide a justification for early retirement.")
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

    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this training session.",
    )

    comment = fields.Text(string="Comment")
    user_can_comment = fields.Boolean(string="Can Comment", compute="_compute_user_can_comment", store=False)


    def _format_date(self, date):
        """
        Format a date into a human-readable string.
        
        Args:
            date (datetime.date): The date to format
            
        Returns:
            str: Formatted date string in user's locale or empty string if no date
        """
        if date:
            return format_date(date, format="long", locale=self.env.user.lang or "en_US")
        return ""
    
    
    @api.model
    def send_notification(self, message, user, title):
        """
        Send a notification to a specific user.
        
        Args:
            message (str): The notification message
            user (res.users): The user to notify
            title (str): The notification title
        """
        self.env['custom.notification'].create({
            'title': title,
            'message': message,
            'user_id': user.id,
        })

    @api.onchange('proposed_retirement_date')
    def _onchange_proposed_retirement_date(self):
        """
        Validate that proposed retirement date is not in the past.
        Triggered when proposed_retirement_date field changes.
        
        Raises:
            ValidationError: If date is in the past
        """    
        if self.proposed_retirement_date and self.proposed_retirement_date <= datetime.now().date():
            raise ValidationError("Proposed retirement date cannot be in the past.")
    

    def action_submit(self):
        """
        Submit the early retirement request for approval.
        Changes state to 'submitted' and notifies CEO users.
        
        Raises:
            ValidationError: If request is not in draft state or date is invalid
        """
        if self.state != 'draft':
            raise ValidationError("Only draft requests can be submitted.")
        ceo_users = self.env.ref('user_group.group_ceo').users
        for record in self:
            if record.proposed_retirement_date and record.proposed_retirement_date <= datetime.now().date():
                raise ValidationError("Proposed retirement date cannot be in the past.")
            record.state = 'submitted'
            record.request_date = datetime.today()
            message = f"{record.employee_name} has requested for early retirement on {record._format_date(record.proposed_retirement_date)}."
            for user in ceo_users:
                self.send_notification(message=message, user=user, title=self._description)
                user.notify_success(message=message,title=self._description)
            self.env.user.notify_success(message="Early Retirement Request Submitted Successfully.", title=self._description)

    

    def action_approve(self):
        """
        Approve an early retirement request.
        Updates employee retirement date and sends notifications.
        
        Raises:
            ValidationError: If request is not in submitted state
        """
        if self.state != 'submitted':
            raise ValidationError("Only submitted requests can be approved.")
        self.state = 'approved'
        self.ceo_state = 'approved'
        self.employee_id.retirement_date = self.proposed_retirement_date
        self.employee_id.retirement_extended = True

        message = f"Your Early Retirement Request has been approved."
        self.send_notification(message=message, user=self.employee_id.user_id, title=self._description)
        self.employee_id.user_id.notify_success(message=message, title=self._description)
        self.env.user.notify_success(message="Early Retirement Request Approved Successfully.", title=self._description)



    def action_reject(self):
        """
        Reject an early retirement request.
        Updates request state and sends notifications.
        
        Raises:
            ValidationError: If request is not in submitted state
        """
        if self.state != 'submitted':
            raise ValidationError("Only submitted requests can be rejected.")
        self.state = 'rejected'
        self.ceo_state = 'approved'

        message = f"Your Early Retirement Request has been rejected."
        self.send_notification(message=message, user=self.employee_id.user_id, title=self._description)
        self.employee_id.user_id.notify_warning(message=message, title=self._description)
        self.env.user.notify_warning(message="Early Retirement Request Rejected.", title=self._description)



    @api.model
    def _compute_user_can_comment(self):
        """
        Compute if current user has permission to comment.
        Sets user_can_comment field based on CEO group membership.
        """
        for record in self:
            record.user_can_comment = self.env.user.has_group("user_group.group_ceo")


    def retire_employee_early(self):
        """
        Process early retirement for approved requests.
        Deactivates employee and user accounts when retirement date is reached.
        """
        for record in self:
            if record.state == 'approved' and self.employee_id.retirement_date and self.employee_id.retirement_date <= datetime.now().date():
                record.employee_id.near_retirement = False
                record.employee_id.is_retired = True
                if record.employee_id.user_id:
                    record.employee_id.user_id.active = False
                record.employee_id.active = False


    def update_retired_employee_early(self):
        """
        Update retirement status for all employees.
        Processes retirement for all approved requests.
        """
        employees = self.search([])
        employees.retire_employee_early()