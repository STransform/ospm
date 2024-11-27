from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

class TransferRequest(models.Model):
    
    _name = "transfer.request"
    _description = "This is the transfer request Model for the OSPM"

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, default=lambda self: self._get_employee())
    department_id = fields.Many2one('hr.department', string="Current Department", compute="_compute_employee_details", store=True)
    department_manager = fields.Many2one('res.users', string="Current Department Manager", compute="_compute_employee_details", store=True)
    new_department_id = fields.Many2one('hr.department', string="New Department", required=True)
    new_department_manager = fields.Many2one('res.users', string="New Department Manager", compute="_compute_new_department_manager", store=True)
    current_job_position = fields.Many2one('hr.job', string="Current Job Position", compute="_compute_employee_details", store=True)
    requested_position = fields.Many2one('hr.job', string="Requested Position", required=True)
    email = fields.Char(string="Email", compute="_compute_employee_details", store=True)
    phone = fields.Char(string="Phone", compute="_compute_employee_details", store=True)
    reason = fields.Text(string="Reason for Transfer", required=True)
    current_dep_comment = fields.Text(string="Current Department Comment")
    new_dep_comment = fields.Text(string="New Department Comment")
    dceo_comment = fields.Text(string="DCEO Comment")
    ceo_comment = fields.Text(string="CEO Comment")

    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved_by_current', 'Current Dept'),
        ('approved_by_new', 'New Dept'),
        ('approved_by_dceo', 'DCEO'),
        ('approved_by_ceo', 'CEO'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft')
    
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this training session.",
    )

    is_current_manager = fields.Boolean(
        string="Is Current Manager", compute="_compute_is_current_manager", store=False
    )
    is_new_manager = fields.Boolean(
        string="Is New Manager", compute="_compute_is_new_manager", store=False
    )
    is_dceo = fields.Boolean(
        string="Is DCEO", compute="_compute_is_dceo", store=False
    )
    is_ceo = fields.Boolean(
        string="Is CEO", compute="_compute_is_ceo", store=False
    )
    is_hr_officer = fields.Boolean(
        string="Is HR Officer", compute="_compute_is_hr_officer", store=False
    )
    is_creator = fields.Boolean(
        string="Is Creator", compute="_compute_is_creator", store=False
    )

    @api.model
    def _get_employee(self):
        """
        Fetch the employee record for the currently logged-in user.
        """
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if not employee:
            raise ValidationError(_("You are not linked to any employee record. Please contact your administrator."))
        return employee.id

    @api.depends('employee_id')
    def _compute_employee_details(self):
        """
        Compute fields based on the employee_id.
        """
        for record in self:
            if record.employee_id:
                if not record.employee_id.department_id:
                    raise ValidationError(_("You are not assigned to any department. Please contact the administrator."))
                
                if not record.employee_id.department_id.manager_id or not record.employee_id.department_id.manager_id.user_id:
                    raise ValidationError(_("Your Current department doesn't have an assigned manager. Please contact the administrator."))

                record.department_id = record.employee_id.department_id
                record.department_manager = record.employee_id.department_id.manager_id.user_id
                record.current_job_position = record.employee_id.job_id
                record.email = record.employee_id.work_email
                record.phone = record.employee_id.work_phone
            else:
                record.department_id = False
                record.department_manager = False
                record.current_job_position = False
                record.email = False
                record.phone = False

    @api.depends('new_department_id')
    def _compute_new_department_manager(self):
        """
        Compute the new department manager based on the selected new_department_id.
        """
        for record in self:
            if record.new_department_id:
                if not record.new_department_id.manager_id or not record.new_department_id.manager_id.user_id:
                    raise ValidationError(_("The selected department does not have a Manager. Please contact the administrator."))
                record.new_department_manager = record.new_department_id.manager_id.user_id
            else:
                record.new_department_manager = False

    @api.depends()
    def _compute_is_current_manager(self):
        self.is_current_manager = self.department_manager.id == self.env.uid

    @api.depends()
    def _compute_is_new_manager(self):
        self.is_new_manager = self.new_department_manager.id == self.env.uid

    @api.depends()
    def _compute_is_dceo(self):
        self.is_dceo = self.env.user.has_group('planning.group_admin_dceo')

    @api.depends()
    def _compute_is_ceo(self):
        self.is_ceo = self.env.user.has_group('planning.group_ceo')
    
    @api.depends()
    def _compute_is_hr_officer(self):
        self.is_hr_officer = self.env.user.has_group('planning.group_hr_officer')
    
    @api.depends()
    def _compute_is_creator(self):
        self.is_creator = self.employee_id.user_id.id == self.env.uid
    
    @api.onchange('new_department_id')
    def _onchange_new_department_id(self):
        if self.status not in ['approved_by_ceo','completed'] and self.new_department_id and self.new_department_id == self.department_id:
            raise ValidationError(_("You cannot transfer to your current department."))

    @api.onchange('requested_position')
    def _onchange_requested_position(self):
        if self.status not in ['approved_by_ceo','completed'] and self.requested_position and self.requested_position == self.current_job_position:
            raise ValidationError(_("You cannot request the same position as your current job position."))
    
    def submit(self):
        if self.status == 'draft':
            self.status = 'submitted'
            return
        raise ValidationError(_("You cannot submit this request."))
    
    def approve_by_current_department(self):
        if self.status == 'submitted' and self.env.user.id == self.department_manager.id:
            self.status = 'approved_by_current'
            return
        raise ValidationError(_("You cannot approve this request."))
    
    def approve_by_new_department(self):
        if self.status == 'approved_by_current' and self.env.user.id == self.new_department_manager.id:
            self.status = 'approved_by_new'
            return
        raise ValidationError(_("You cannot approve this request."))
    
    def approve_by_dceo(self):
        if self.status == 'approved_by_new' and self.env.user.has_group('planning.group_admin_dceo'):
            self.status = 'approved_by_dceo'
            return
        raise ValidationError(_("You cannot approve this request."))
    
    def approve_by_ceo(self):
        if self.status == 'approved_by_dceo' and self.env.user.has_group('planning.group_ceo'):
            self.status = 'approved_by_ceo'
            return
        raise ValidationError(_("You cannot approve this request."))
    
    def reject(self):
        if self.status == 'submitted':
            if self.department_manager.id != self.env.uid:
                raise ValidationError(_("You are not the Manager of this Department"))
            self.status = 'rejected'
        elif self.status == 'approved_by_current':
            if self.new_department_manager.id != self.env.uid:
                raise ValidationError(_("You are not the Manager of this Department"))
            self.status = 'rejected'
        elif self.status == 'approved_by_new':
            if not self.env.user.has_group('planning.group_admin_dceo'):
                raise ValidationError(_("You are not the D/CEO, Administration & Marketing Division"))
            self.status = 'rejected'
        elif self.status == 'approved_by_dceo':
            if not self.env.user.has_group('planning.group_admin_ceo'):
                raise ValidationError(_("You are not the CEO"))
            self.status = 'rejected'

    def hr_office_proceed(self):
        if not self.status == 'approved_by_ceo':
            raise ValidationError(_("You cannot proceed with this request."))
        if not self.env.user.has_group('planning.group_hr_office'):
            raise ValidationError(_("You are not the HR Officer."))
        # self.employee_id.department_id = self.new_department_id.id
        # self.employee_id.job_id = self.requested_position.id

      
        self.employee_id.write({
            'department_id': self.new_department_id.id,
            'job_id': self.requested_position.id
        })

        self.env['transfer.history'].create({
        'employee_id': self.employee_id.id,
        'transfer_date': fields.Datetime.now(),
        'from_department_id': self.department_id.id,
        'to_department_id': self.new_department_id.id,
        'from_position_id': self.current_job_position.id,
        'to_position_id': self.requested_position.id,
        'reason': self.reason,
        'approved_by': self.env.user.id,
        })
        if self.new_department_id != self.employee_id.department_id:
            raise ValidationError(_("Please Update The employee Information before making the transfer Completed"))
        if self.requested_position != self.employee_id.job_id:
            raise ValidationError(_("Please Update The employee Information before making the transfer Completed"))

        
        self.status = 'completed'