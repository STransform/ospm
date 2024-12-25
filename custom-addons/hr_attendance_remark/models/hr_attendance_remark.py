from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class HrAttendanceRemark(models.Model):
    _name = 'hr.attendance.remark'
    _description = 'Attendance Remark'

    attendance_id = fields.Many2one(
        'hr.attendance', 
        string="Attendance", 
        required=True, 
        ondelete='cascade', 
        index=True,
        domain=lambda self: [
        ('employee_id.user_id', '=', self.env.user.id),  # Only current employees
        ('attendance_status', 'in', ['late_in', 'early_out', 'absent', 'late_in_and_early_out'])  # Attendance statuses
    ]
    )  # Link to hr.attendance
    
    remark = fields.Text(string="Remark")
    employee_id = fields.Many2one(
        related="attendance_id.employee_id",
        string="Employee",
        store=True,
        readonly=True,
    )  # Automatically get employee_id from hr.attendance

    manager_id = fields.Many2one(string="Approver", related="employee_id.parent_id", store=True, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='State', default='draft', readonly=True, copy=False, tracking=True)

    is_manager = fields.Boolean(
        string='Is Manager',
        compute='_compute_is_manager',
        store=False
    )
    is_creator = fields.Boolean(string="Is Creator", compute="_compute_is_creator", store=False)

    attendance_status = fields.Selection(
        selection=lambda self: self.env['hr.attendance']._fields['attendance_status'].selection,
        string="Attendance Status",
        related="attendance_id.attendance_status",
        store=True,
        readonly=True
    )
    _sql_constraints = [
        ('attendance_id_unique', 
         'unique(attendance_id)', 
         'The selected attendance ID already has a remark.')
    ]

    # add notification function 
    @api.model
    def send_notification(self, message, user, title, model,res_id):
        self.env['custom.notification'].create({
            'title': title,
            'message': message,
            'user_id': user.id,
            'action_model': model,
            'action_res_id': res_id
        })


    @api.depends('create_uid')
    def _compute_is_creator(self):
        for record in self:
            record.is_creator = record.create_uid.id == self.env.user.id


    @api.model
    def create(self, vals):
        """Ensure that only the logged-in user's attendance can be added"""
        attendance = self.env['hr.attendance'].browse(vals.get('attendance_id'))
        if attendance.employee_id.user_id != self.env.user:
            raise ValidationError("You can only add remarks for your own attendance.")
        return super(HrAttendanceRemark, self).create(vals)

    @api.depends('manager_id')
    def _compute_is_manager(self):
        for record in self:
            record.is_manager = record.manager_id.user_id.id == self.env.uid



    # approved by manager
    def action_approve(self):
        """Approve the remark and update the corresponding attendance record"""
        for record in self:
            if record.attendance_id:
                # Write the remark to hr.attendance using sudo
                record.attendance_id.sudo().write({'remark': record.remark})
                record.state = 'approved'
            else:
                raise UserError("Attendance record not found. Unable to approve the remark.")

            title = "Remark Approved"
            message = f"Your remark has been approved."
            record.employee_id.user_id.notify_success(title=title, message=message)
            self.send_notification(message, record.employee_id.user_id, title, model = self._name, res_id = self.id)
            self.env.user.notify_success("Remark Approved!")

    

    # rejected by manager
    def action_refuse(self):
        """Reject the remark"""
        for record in self:
            record.state = 'rejected'

            title = "Remark Refused"
            message = f"Your Remark has been rejected."
            user = self.create_uid
            self.send_notification(message=message, user=user, title=title, model=self._name, res_id=self.id)
            self.env.user.notify_success(title=title, message=message)


    def action_submit(self):
        """Submit the remark"""
        for record in self:
            record.state = "submitted"

            service_manager = record.manager_id.user_id
            title = "Attendance Remark Submitted"
            message = f"{record.employee_id.name} Remark Submitted for being {record.attendance_status}"
            self.send_notification(message, service_manager, title, model = self._name, res_id = self.id)



