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
    position_id = fields.Many2one('hr.job', string="Position",  store=True)

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

    def action_property_approve(self):
        """Approve the property stage."""
        if self.department_approval != 'approved':
            raise ValidationError(_("Cannot approve property clearance until department clearance is approved."))
        self.property_approval = 'approved'
        self.state = 'in_progress'

    def action_finance_approve(self):
        """Approve the finance stage."""
        if self.property_approval != 'approved':
            raise ValidationError(_("Cannot approve finance clearance until property clearance is approved."))
        self.finance_approval = 'approved'
        self.state = 'in_progress'

    def action_hr_approve(self):
        """Approve the HR stage."""
        if self.finance_approval != 'approved':
            raise ValidationError(_("Cannot approve HR clearance until finance clearance is approved."))
        self.hr_approval = 'approved'
        self.state = 'approved'

    def action_reapprove_department(self):
        """Reapprove the department stage after rejection."""
        if self.department_approval != 'rejected':
            raise ValidationError(_("Department clearance is not rejected."))
        self.department_approval = 'approved'
        self.state = 'in_progress'

    def action_reapprove_property(self):
        """Reapprove the property stage after rejection."""
        if self.property_approval != 'rejected':
            raise ValidationError(_("Property clearance is not rejected."))
        self.property_approval = 'approved'
        self.state = 'in_progress'

    def action_reapprove_finance(self):
        """Reapprove the finance stage after rejection."""
        if self.finance_approval != 'rejected':
            raise ValidationError(_("Finance clearance is not rejected."))
        self.finance_approval = 'approved'
        self.state = 'in_progress'

    def action_reapprove_hr(self):
        """Reapprove the HR stage after rejection."""
        if self.hr_approval != 'rejected':
            raise ValidationError(_("HR clearance is not rejected."))
        self.hr_approval = 'approved'
        self.state = 'approved'
    def action_reject_department(self):
        """Reject the department stage."""
        self.department_approval = 'rejected'
        self.state = 'rejected'

    def action_reject_property(self):
        """Reject the property stage."""
        self.property_approval = 'rejected'
        self.state = 'rejected'

    def action_reject_finance(self):
        """Reject the finance stage."""
        self.finance_approval = 'rejected'
        self.state = 'rejected'

    def action_reject_hr(self):
        """Reject the HR stage."""
        self.hr_approval = 'rejected'
        self.state = 'rejected'

    def action_save_clearance(self):
        for record in self:
            # Saving the record 
            record.write({
                'name': record.name,
                'employee_id': record.employee_id.id,
                'department_id': record.department_id.id,
                'position_id': record.position_id.id,
                'documents': [(6, 0, record.documents.ids)],
                'reason': record.reason,
                'department_approval': record.department_approval,
                'property_approval': record.property_approval,
                'finance_approval': record.finance_approval,
                'hr_approval': record.hr_approval,
            })
          
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'You have successfully saved the record!',
                'type': 'success',
                'sticky': False,  # this makes the success button disappear after a few seconds
            }
        }