"""
This module defines the EducationDepartmentRequest model which handles education program requests for departments.
It inherits from mail.thread and mail.activity.mixin for communication features.
The model manages the lifecycle of education program requests including submission, approval and rejection flows.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class EducationDepartmentRequest(models.Model):
    """
    Model for managing education department requests.
    Handles education programs, approvals, and notifications between departments and HR.
    
    Inherits:
        mail.thread: For message tracking
        mail.activity.mixin: For activity management
    """
    _name = 'education.department.request'
    _description = 'Education Department Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'department_id'

    @api.model
    def year_selection(self):
        """
        Generate list of years for selection field.
        
        Returns:
            list: List of tuples containing (year, year) for next 10 years
        """
        year = datetime.now().year
        list_of_years = []

        for i in range(10):
            list_of_years.append((str(year),str(year)))
            year += 1

        return list_of_years 

    name = fields.Char(string="Request Name", compute="_compute_name", store=True)
    education_programs = fields.One2many('education.program', 'education_id', string='Education Programs')
    description = fields.Text(string='Description')
    department_id = fields.Many2one('hr.department', string='Department', required=True, readonly=True, default=lambda self: self._get_default_department())
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this education program.",
        required=True,
    )
    year = fields.Selection(year_selection,string="Year", required=True)
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='draft',
        store=True,
    )

    hr_reason = fields.Text(string="HR Reason")
    is_resubmitted = fields.Boolean(string="Is Resubmitted", default=False)
    is_department_manager = fields.Boolean(
        string="Is Department Manager",
        compute="_compute_is_department_manager",
        search="_search_is_department_manager",
        store=False,
    )
    is_hr_office = fields.Boolean(
        string="Is Hr Officer",
        compute="_compute_is_hr_office",
        store=False,
    )
    hr_reason_is_visible = fields.Boolean(
        string="HR Reason Visibility",
        compute="_compute_hr_reason_visibility",
        store=False,
    )

    total_employee_count = fields.Integer(
        string="Total Employees",
        compute="_compute_total_employee_count",
        store=True,
        help="Total number of employees across all education programs."
    )


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


    @api.depends('year','department_id')
    def _compute_name(self):
        """
        Compute the name of the education request based on department and year.
        
        Dependencies:
            year (Selection): Selected year
            department_id (Many2one): Department reference
        """
        for record in self:
            record.name = f"{record.department_id.name} Education Plan for {record.year}" if record.year else f"{record.department_id.name} Education Plan for -"


    @api.depends('education_programs.employee_count')
    def _compute_total_employee_count(self):
        """
        Compute total number of employees across all education programs.
        
        Dependencies:
            education_programs.employee_count (Integer): Count of employees per program
        """
        for record in self:
            record.total_employee_count = sum(program.employee_count for program in record.education_programs)


    @api.model
    def _compute_hr_reason_visibility(self):
        """
        Determine visibility of HR reason field based on user groups and request state.
        """
        for record in self:
            if self.env.user.has_group("user_group.group_hr_director"):
                record.hr_reason_is_visible = record.state != 'draft' or record.is_resubmitted
            else:
                record.hr_reason_is_visible = record.state not in ['draft', 'submitted'] or record.is_resubmitted


    @api.model
    def _compute_is_hr_office(self):
        """
        Check if current user belongs to HR office group.
        """
        for record in self:
            record.is_hr_office = self.env.user.has_group("user_group.group_hr_director")


    @api.depends('department_id')
    def _compute_is_department_manager(self):
        """
        Check if current user is department manager for this request.
        """
        for record in self:
            record.is_department_manager = self.env.user.has_group("user_group.group_department_manager") and record.department_id.manager_id.user_id.id == self.env.uid


    @api.model
    def _get_default_department(self):
        """
        Fetch the department of currently logged-in user.
        
        Returns:
            int: Department ID
            
        Raises:
            ValidationError: If no department is assigned to current user
        """
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if not employee or not employee.department_id:
            raise ValidationError("No department is assigned to the current user.")
        return employee.department_id.id


    def _search_is_department_manager(self, operator, value):
        """
        Custom search function for is_department_manager field.
        
        Args:
            operator (str): Search operator ('=' or '!=')
            value (bool): Search value
            
        Returns:
            list: Domain for search
            
        Raises:
            ValueError: If operator not supported
        """
        if operator not in ['=', '!=']:
            raise ValueError("Operator not supported for this field.")
        
        user_id = self.env.uid
        # Query departments where the logged-in user is the manager
        department_ids = self.env['hr.department'].search([('manager_id.user_id', '=', user_id)]).ids

        # Match records with the queried departments
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('department_id', 'in', department_ids)]
        else:
            return [('department_id', 'not in', department_ids)]
    

    def action_submit(self):
        """
        Submit education request for approval.
        
        Raises:
            ValidationError: If user not authorized or request not in draft state
        """
        if not self.is_department_manager or self.state != 'draft':
            raise ValidationError(_("You can not Submit this Education Request."))
        self.state = 'submitted'
        message = f"The Department Manager has submitted the Education plan for {self.year}"
        hr_office_users = self.env.ref('user_group.group_hr_director').users

        for user in hr_office_users:
            self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
            user.notify_info(message=message, title=self._description)

        self.env.user.notify_success(message="Request Submitted Successfully", title=self._description)


    def action_approve_request(self):
        """
        Approve submitted education request.
        
        Raises:
            ValidationError: If user not authorized or request not in submitted state
        """
        if not self.is_hr_office or self.state != 'submitted':
            raise ValidationError(_("You can not Approve this Request"))
        self.state = 'approved'
        message = f"The Hr Office has Approved the Education plan for {self.year}"

        if self.department_id.manager_id.user_id:
            self.send_notification(message=message, user=self.department_id.manager_id.user_id, title=self._description, model=self._name, res_id=self.id)
            self.department_id.manager_id.user_id.notify_info(message="Request Approved Successfully", title=self._description)

        self.env.user.notify_success(message="Request Approved Successfully", title=self._description)


    def action_reject_request(self):
        """
        Reject submitted education request.
        
        Raises:
            ValidationError: If user not authorized, request not in submitted state,
                           or rejection reason not provided
        """
        if not self.is_hr_office or self.state != 'submitted':
            raise ValidationError(_("You can not Reject this Request"))
        if not self.hr_reason:
            raise ValidationError(_("Please Enter Rejection Reason"))
        self.state = 'rejected'
        message = f"The Hr Office has Rejected the Education plan for {self.year}"
        if self.department_id.manager_id.user_id:
            self.send_notification(message=message, user=self.department_id.manager_id.user_id, title=self._description, model=self._name, res_id=self.id)
            self.department_id.manager_id.user_id.notify_warning(message="Request Rejected Successfully", title=self._description)
        
        self.env.user.notify_warning(message="Request Rejected Successfully", title=self._description)
    

    def action_resubmit(self):
        """
        Resubmit rejected education request.
        
        Raises:
            ValidationError: If user not authorized or request not in rejected state
        """
        if not self.is_department_manager or self.state != 'rejected':
            raise ValidationError(_("You can not Resubmit this Education Request."))
        self.state = 'submitted'
        self.is_resubmitted = True
        message = f"The Department Manager has Resubmitted the Education plan for {self.year}"
        hr_office_users = self.env.ref('user_group.group_hr_director').users

        for user in hr_office_users:
            self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
            user.notify_info(message=message, title=self._description)

        self.env.user.notify_success(message="Request Resubmitted Successfully", title=self._description)
    

    _sql_constraints = [
        (
            'unique_year_per_department',
            'UNIQUE(year, department_id)',
            'The Year must be unique for each department!'
        ),
    ]