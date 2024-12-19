from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class HrEducationRequest(models.Model):
    _name = 'hr.education.request'
    _description = 'HR Education Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    @api.model
    def year_selection(self):
        year = datetime.now().year
        list_of_years = []

        for i in range(10):
            list_of_years.append((str(year),str(year)))
            year += 1

        return list_of_years 

    name = fields.Char(string="Request Name", compute="_compute_name", store=True)
    education_programs = fields.One2many('hr.education.program', 'education_id', string='Education Programs')
    description = fields.Text(string='Description')
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this education program.",
    )

    year = fields.Selection(year_selection, string="Year", required=True)
    planning_reason = fields.Text(string="Planning Reason")
    ceo_reason = fields.Text(string="CEO Reason")

    combined_state = fields.Selection(
        string="Combined State",
        selection=[('pending','Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default = 'pending',
        store=True
    )
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'), ('submitted', 'Submitted'), ('planning_approved','Approved by Planning'),('approved', 'Approved'), ('rejected', 'Rejected')],
        default='draft',
        store=True,
    )
    is_resubmitted = fields.Boolean(string="Is Resubmitted", default=False)
    planning_reason_is_visible = fields.Boolean(string="Planning Reason Visibility", compute="_compute_planning_reason_visibility",store=False)
    ceo_reason_is_visible = fields.Boolean(string="CEO Reason Visibility", compute="_compute_ceo_reason_visibility",store=False)
    is_ceo = fields.Boolean(string="Is CEO", compute="_compute_is_ceo", store=False)
    is_planning = fields.Boolean(string="Is Planning", compute="_compute_is_planning", store=False)
    is_hr_office = fields.Boolean(string="Is HR Office", compute="_compute_is_hr_office", store=False)
    is_editable = fields.Boolean(string="Is Editable", compute="_compute_is_editable", store=False)

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


    @api.model
    def _compute_planning_reason_visibility(self):
        for record in self:
            if self.env.user.has_group("user_group.group_planning_directorate"):
                record.planning_reason_is_visible = record.state != 'draft' or record.is_resubmitted
            else:
                record.planning_reason_is_visible = record.state not in ['draft', 'submitted'] or record.is_resubmitted

    @api.model
    def _compute_ceo_reason_visibility(self):
        for record in self:
            if self.env.user.has_group("user_group.group_ceo"):
                record.ceo_reason_is_visible = record.state not in ['draft', 'submitted'] or record.is_resubmitted
            else:
                record.ceo_reason_is_visible = record.state not in ['draft', 'submitted', 'planning_approved'] or record.is_resubmitted

    @api.model
    def _compute_is_ceo(self):
        for record in self:
            record.is_ceo = self.env.user.has_group("user_group.group_ceo")
    
    @api.model
    def _compute_is_planning(self):
        for record in self:
            record.is_planning = self.env.user.has_group("user_group.group_planning_directorate")

    @api.model
    def _compute_is_hr_office(self):
        for record in self:
            record.is_hr_office = self.env.user.has_group("user_group.group_hr_director")

    @api.model
    def _compute_is_editable(self):
        for record in self:
            record.is_editable = self.env.user.has_group("user_group.group_hr_director") and (record.state == 'draft' or record.state == 'rejected')

    @api.depends('education_programs.employee_count')
    def _compute_total_employee_count(self):
        for record in self:
            record.total_employee_count = sum(program.employee_count for program in record.education_programs)

    @api.depends('year')
    def _compute_name(self):
        for record in self:
            record.name = f"HR Office Education Plan for {record.year}" if record.year else "HR Office Education Plan for -"
    
    def action_submit(self):
        if not self.env.user.has_group("user_group.group_hr_director") or self.state != 'draft':
            raise ValidationError(_("You can not Submit this Education Request."))
        self.state = 'submitted'
        self.combined_state = 'pending'
        planning_directors = self.env.ref('user_group.group_planning_directorate').users
        message = f"The Hr office has submitted the Education plan for {self.year}"
        for user in planning_directors:
            self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
            user.notify_success(title=self._description,message="Request Submitted Successfully")

        self.env.user.notify_success(title=self._description,message="Request Submitted Successfully")
        

    def action_approve_ceo(self):
        if not self.env.user.has_group("user_group.group_ceo") or self.state != 'planning_approved':
            raise ValidationError(_("You can not Approve this Request"))
        self.state = 'approved'
        self.combined_state = 'approved'
        planning_directors = self.env.ref('user_group.group_planning_directorate').users
        message = f"The CEO has Approved the Education plan for {self.year}"
        for user in planning_directors:
            self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
            user.notify_success(title=self._description,message="Request Approved Successfully")

        self.send_notification(message=message, user=self.create_uid, title=self._description, model=self._name, res_id=self.id)
        self.create_uid.notify_success(title=self._description,message="Request Approved Successfully")
        self.env.user.notify_success(title=self._description,message="Request Approved Successfully")


    def action_reject_ceo(self):
        if not self.env.user.has_group("user_group.group_ceo") or self.state != 'planning_approved':
            raise ValidationError(_("You can not Rejected this Request"))
        if not self.ceo_reason:
            raise ValidationError(_("Please Enter Rejection Reason"))
        self.state = 'rejected'
        self.combined_state = 'rejected'
        planning_directors = self.env.ref('user_group.group_planning_directorate').users
        message = f"The CEO has Rejected the Education plan for {self.year}"
        for user in planning_directors:
            self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
            user.notify_warning(title=self._description,message="Request Rejected Successfully")

        self.send_notification(message=message, user=self.create_uid, title=self._description, model=self._name, res_id=self.id)
        self.create_uid.notify_warning(title=self._description,message="Request Rejected Successfully")
        self.env.user.notify_warning(title=self._description,message="Request Rejected Successfully")

    def action_approve_planning(self):
        if not self.env.user.has_group("user_group.group_planning_directorate") or self.state != 'submitted':
            raise ValidationError(_("You can not Approve this Request"))
        self.state = 'planning_approved'
        self.combined_state = 'pending'
        ceo_users = self.env.ref('user_group.group_ceo').users
        message = f"The Planning Director has Approve the Education plan for {self.year}"
        for user in ceo_users:
            self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
            user.notify_success(title=self._description,message="Request Approved Successfully")

        self.send_notification(message=message, user=self.create_uid, title=self._description, model=self._name, res_id=self.id)
        self.create_uid.notify_success(title=self._description,message="Request Approved Successfully")
        self.env.user.notify_success(title=self._description,message="Request Approved Successfully")


    def action_reject_planning(self):
        if not self.env.user.has_group("user_group.group_planning_directorate") or self.state != 'submitted':
            raise ValidationError(_("You can not Rejected this Request"))
        if not self.planning_reason:
            raise ValidationError(_("Please Enter Rejection Reason"))
        self.state = 'rejected'
        self.combined_state = 'rejected'
        ceo_users = self.env.ref('user_group.group_ceo').users
        message = f"The Planning Director has Rejected the Education plan for {self.year}"
        for user in ceo_users:
            self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
            user.notify_warning(title=self._description,message="Request Rejected Successfully")

        self.send_notification(message=message, user=self.create_uid, title=self._description, model=self._name, res_id=self.id)
        self.create_uid.notify_warning(title=self._description,message="Request Rejected Successfully")
        self.env.user.notify_warning(title=self._description,message="Request Rejected Successfully")

            
    def action_resubmit(self):
        if not self.env.user.has_group("user_group.group_hr_director") or self.state != 'rejected':
            raise ValidationError(_("You can not Resubmit this Education Request."))
        self.state = 'submitted'
        self.combined_state = 'pending'
        self.is_resubmitted = True
        planning_directors = self.env.ref('user_group.group_planning_directorate').users
        message = f"The Hr office has Resubmitted the Education plan for {self.year}"
        for user in planning_directors:
            self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
            user.notify_success(title=self._description,message="Request Resubmitted Successfully")

        self.env.user.notify_success(title=self._description,message="Request Resubmitted Successfully")

    _sql_constraints = [
        (
            'unique_year',
            'UNIQUE(year)',
            'The Year must be unique'
        ),
    ]