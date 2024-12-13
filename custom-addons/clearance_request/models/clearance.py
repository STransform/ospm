from odoo import models, fields, api, _
from odoo.exceptions import  ValidationError

class Clearance(models.Model):
    _name = 'employee.clearance'
    _description = 'Employee Clearance Workflow'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    name = fields.Char(string="Clearance Request", required=True, tracking=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string="Department",store=True)
    job_id = fields.Many2one('hr.job', string="Position",  store=True)

    documents = fields.Many2many('ir.attachment', string='Attachments', help="Attach documents related to clearance request")
    reason = fields.Selection(
        [('resignation', 'Resignation'), ('retirement', 'Retirement'), ('termination', 'Termination'),('contract', 'End of Contract'),('transfer', 'Transfer')],
        string="Reason for Clearance",
        required=True,
        tracking=True
    )
    date_requested = fields.Date(string="Requested Date", default=fields.Date.today, tracking=True)
    department_approval = fields.Selection(
        [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        string="Department Approval",
        default='pending',
        tracking=True
    )
     # to make the department approval button only visible at this state

    is_department_approve = fields.Boolean(string="Is Department Approve", compute="_compute_is_department_approve", store=False)
    is_property_approve = fields.Boolean(string="Is Property Approve", compute="_compute_is_property_approve", store=False)
    is_finance_approve = fields.Boolean(string="Is Finance Approve", compute="_compute_is_finance_approve", store=False)
    is_hr_approve = fields.Boolean(string="Is Hr Approve", compute="_compute_is_hr_approve", store=False)
    show_save_button = fields.Boolean(
        compute='_compute_show_save_button', string="Show Save Button"
    )
    is_creator = fields.Boolean(string="Is Creator", compute="_compute_is_creator", store=False)
    

    @api.model
    def _compute_is_creator(self):
        if self.employee_id:
            self.is_creator = self.employee_id.user_id.id == self.env.user.id
     # to make save button only visible at creation step,other that its invisible
    user_id = fields.Many2one('res.users', string='User')
    user_in_group = fields.Boolean(compute='_compute_user_in_group', store=False)
    @api.depends('user_id')
    def _compute_user_in_group(self):
        group = self.env.ref('clearance_request.group_department_approval', raise_if_not_found=False)
        if group:
            self.user_in_group = self.env.user in group.users
        else:
            self.user_in_group = False
     # to make save button only visible at creation step,other that its invisible
     
     # to make the department approval button only visible at this state
    @api.model
    def _get_default_employee(self):
        """This method will return the currently logged-in user's employee record."""
        user = self.env.user
        employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if employee:
            # Automatically set the department and position when the employee is found
            self._onchange_employee_id()  # Trigger the onchange for department and position
            return employee.id
        return False 

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Set the department and position based on the selected employee."""
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id
        else:
            self.department_id = False
            self.job_id = False
    @api.model
    def _compute_is_department_approve(self):
        self.is_department_approve = self.env.user.has_group("clearance_request.group_department_approval")
    @api.model
    def _compute_is_property_approve(self):
        self.is_property_approve = self.env.user.has_group("clearance_request.group_property_approval")
    @api.model
    def _compute_is_finance_approve(self):
        self.is_finance_approve = self.env.user.has_group("clearance_request.group_finance_approval")
    @api.model
    def _compute_is_hr_approve(self):
        self.is_hr_approve = self.env.user.has_group("clearance_request.group_hr_approval")
    
    property_approval = fields.Selection(
        [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        string="Property Approval",
        default='pending',
        tracking=True
    )
    finance_approval = fields.Selection(
        [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        string="Finance Approval",
        default='pending',
        tracking=True
    )
    hr_approval = fields.Selection(
        [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        string="HR Approval",
        default='pending',
        tracking=True
    )
    state = fields.Selection(
        [('draft', 'Draft'), ('in_progress', 'In Progress'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        string="Status",
        default='draft',
        tracking=True
    )
    
    @api.onchange('department_approval', 'property_approval', 'finance_approval')
    def _check_clearance_status(self):
        if (self.department_approval == 'approved' and
            self.property_approval == 'approved' and
            self.finance_approval == 'approved'):
            self.hr_approval = 'pending'
            self.state = 'in_progress'
            
    

    def action_department_approve(self):
        """Approve the department stage."""
        if self.department_approval != 'pending':
            raise ValidationError(_("Department approval has already been processed."))
        self.department_approval = 'approved'
        self.state = 'in_progress'
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Department stage approved successfully!',
                    'type': 'success',
                    'sticky': False,
                }
            }


    def action_property_approve(self):
        """Approve the property stage."""
        if self.department_approval != 'approved':
            raise ValidationError(_("Cannot approve property clearance until department clearance is approved."))
        self.property_approval = 'approved'
        self.state = 'in_progress'
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Property stage approved successfully!',
                    'type': 'success',
                    'sticky': False,
                }
            }

    def action_finance_approve(self):
        """Approve the finance stage."""
        if self.property_approval != 'approved':
            raise ValidationError(_("Cannot approve finance clearance until property clearance is approved."))
        self.finance_approval = 'approved'
        self.state = 'in_progress'
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Finance stage approved successfully!',
                    'type': 'success',
                    'sticky': False,
                }
            }

    def action_hr_approve(self):
        """Approve the HR stage."""
        if self.finance_approval != 'approved':
            raise ValidationError(_("Cannot approve HR clearance until finance clearance is approved."))
        self.hr_approval = 'approved'
        self.state = 'approved'
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'HR stage approved successfully!',
                    'type': 'success',
                    'sticky': False,
                }
            }

    def action_reapprove_department(self):
        """Reapprove the department stage after rejection."""
        if self.department_approval != 'rejected':
            raise ValidationError(_("Department clearance is not rejected."))
        self.department_approval = 'approved'
        self.state = 'in_progress'
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Department stage approved successfully!',
                    'type': 'success',
                    'sticky': False,
                }
            }

    def action_reapprove_property(self):
        """Reapprove the property stage after rejection."""
        if self.property_approval != 'rejected':
            raise ValidationError(_("Property clearance is not rejected."))
        self.property_approval = 'approved'
        self.state = 'in_progress'
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Property stage approved successfully!',
                    'type': 'success',
                    'sticky': False,
                }
            }

    def action_reapprove_finance(self):
        """Reapprove the finance stage after rejection."""
        if self.finance_approval != 'rejected':
            raise ValidationError(_("Finance clearance is not rejected."))
        self.finance_approval = 'approved'
        self.state = 'in_progress'
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Finance stage approved successfully!',
                    'type': 'success',
                    'sticky': False,
                }
            }

    def action_reapprove_hr(self):
        """Reapprove the HR stage after rejection."""
        if self.hr_approval != 'rejected':
            raise ValidationError(_("HR clearance is not rejected."))
        self.hr_approval = 'approved'
        self.state = 'approved'
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'HR stage approved successfully!',
                    'type': 'success',
                    'sticky': False,
                }
            }
    def action_reject_department(self):
        """Reject the department stage."""
        self.department_approval = 'rejected'
        self.state = 'rejected'
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Rejected',
                    'message': 'Department stage rejected.',
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def action_reject_property(self):
        """Reject the property stage."""
        self.property_approval = 'rejected'
        self.state = 'rejected'
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Rejected',
                    'message': 'Property stage rejected.',
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def action_reject_finance(self):
        """Reject the finance stage."""
        self.finance_approval = 'rejected'
        self.state = 'rejected'
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Rejected',
                    'message': 'Finance stage rejected.',
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def action_reject_hr(self):
        """Reject the HR stage."""
        self.hr_approval = 'rejected'
        self.state = 'rejected'
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Rejected',
                    'message': 'HR stage rejected.',
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def action_save_clearance(self):
        for record in self:
            
            # Ensure department and position are set if not already set
            if not record.department_id:
                record.department_id = record.employee_id.department_id
            if not record.job_id:
                record.job_id = record.employee_id.job_id

            # Prepare the fields to write, only if they are not empty
            values_to_write = {
                'name': record.name,
                'employee_id': record.employee_id.id,
                'documents': [(6, 0, record.documents.ids)],
                'reason': record.reason,
                'department_approval': record.department_approval,
                'property_approval': record.property_approval,
                'finance_approval': record.finance_approval,
                'hr_approval': record.hr_approval,
            }

            # Only write the department and job if they are not set already
            if record.department_id:
                values_to_write['department_id'] = record.department_id.id
            if record.job_id:
                values_to_write['job_id'] = record.job_id.id

            # Write the record data explicitly
            record.write(values_to_write)

            # Explicitly refresh the record in memory to reflect changes in the form
            record.refresh()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'name': 'Employee Clearance',
            'res_model': 'employee.clearance',
            'view_mode': 'tree,form',  # Show list view and allow switching to form view
            'target': 'current',       # Open in the current window
            'params': {
                'title': 'Success',
                'message': 'You have successfully saved the record!',
                'type': 'success',
                'sticky': False,  # this makes the success button disappear after a few seconds
            }
        }


