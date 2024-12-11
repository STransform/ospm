from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EmployeeComplaint(models.Model):
    _name = 'employee.complaint'
    _description = 'Employee Complaint'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Complaint Reference', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True, default=lambda self: self._get_default_employee())
    issue_type = fields.Selection([
        ('rules', 'Rule Interpretation'),
        ('benefits', 'Benefit Utilization'),
        ('rights', 'Rights Violation'),
        ('environment', 'Work Environment'),
        ('promotion', 'Promotion'),
        ('position', 'Position Allocation'),
        ('evaluation', 'Evaluation'),
        ('other', 'Other')
    ], string='Complain Type', required=True, tracking=True)
    description = fields.Text(string='Description', required=True, tracking=True)
    documents = fields.Many2many('ir.attachment', string='Attachments', help="Attach documents related to the complaint")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('legal_reviewed', 'Legal Reviewed'),
        ('accept_legal_review', 'Accept Legal Review'),
        ('reject_legal_review', 'Reject Legal Reviewed'),
        ('ceo_reviewed', 'CEO Reviewed'),
        ('accept_ceo_review', 'Accept CEO Review'),
        ('reject_ceo_review', 'Reject CEO Reviewed')
    ], default='draft', string='Status', tracking=True)
    decision_by_legalservice = fields.Text(
        string='Legal Service Decision', 
        readonly=True, 
        states={'legal_reviewed': [('readonly', False)]},
    )
    decision_by_ceo = fields.Text(
        string='CEO Decision', 
        readonly=True, 
        states={'ceo_reviewed': [('readonly', False)]},
    )
    created_on = fields.Datetime(string='Created On', default=fields.Datetime.now)
    _sql_constraints = [
        ('unique_case_reference', 'unique(name)', 'The Case Reference must be unique.')
    ]
    
    is_creator = fields.Boolean(string="Is Creator", compute="_compute_is_creator", store=False)
    is_ceo = fields.Boolean(string="Is CEO", compute="_compute_is_ceo", store=False)
    is_legal_service = fields.Boolean(string="Is Legal Service", compute="_compute_is_legal_service", store=False)


    @api.model
    def _compute_is_creator(self):
        if self.employee_id:
            self.is_creator = self.employee_id.user_id.id == self.env.user.id
    
    @api.model
    def _compute_is_ceo(self):
        self.is_ceo = self.env.user.has_group("complaint_handling.group_ceo")

    @api.model
    def _compute_is_legal_service(self):
        self.is_legal_service = self.env.user.has_group("complaint_handling.group_legal_servicedepartment")

    # for default logged in user user,so that initiator is automatically populated from logged in user...
    @api.model
    def _get_default_employee(self):
        """This method will return the currently logged-in user's employee record."""
        user = self.env.user
        employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if employee:
            return employee.id
        return False  # Or handle the case when no employee is found for the user

    def _check_access(self, allowed_groups):
        """Check if the current user belongs to one of the allowed groups."""
        if not self.env.user.has_group(allowed_groups):
            raise ValidationError(_("You do not have the access rights to perform this action."))

    def action_submit(self):
        self._check_access('base.group_user')  # Only initiator (regular users)
        if self.state != 'draft':
            raise ValidationError(_("Only complaints in draft state can be submitted to Legal Service."))
        self.state = 'submitted'

    def action_legal_review(self):
        self._check_access('complaint_handling.group_legal_servicedepartment')  # Legal department group
        if self.state != 'submitted':
            raise ValidationError(_("Only complaints in submitted state can be legal reviewed."))
        self.state = 'legal_reviewed'

    def action_accept_legal_review(self):
        self._check_access('base.group_user')  # Only initiator (regular users)
        if self.state != 'legal_reviewed':
            raise ValidationError(_("Legal reviewed must be done first!"))
        self.state = 'accept_legal_review'

    def action_reject_legal_review(self):
        self._check_access('base.group_user')  # Only initiator (regular users)
        if self.state != 'legal_reviewed':
            raise ValidationError(_("Legal reviewed must be done first!"))
        self.state = 'reject_legal_review'

    def action_ceo_review(self):
        self._check_access('complaint_handling.group_ceo')  # CEO group
        if self.state != 'legal_reviewed' and self.state not in ['accept_legal_review', 'reject_legal_review']:
            raise ValidationError(_("Legal reviewed must be done first!"))
        self.state = 'ceo_reviewed'

    def action_accept_ceo_review(self):
        self._check_access('base.group_user')  # Only initiator (regular users)
        if self.state != 'ceo_reviewed':
            raise ValidationError(_("Legal and CEO reviews must be completed before proceeding to this stage."))
        self.state = 'accept_ceo_review'

    def action_reject_ceo_review(self):
        self._check_access('base.group_user')  # Only initiator (regular users)
        if self.state != 'ceo_reviewed':
            raise ValidationError(_("Legal and CEO reviews must be completed before proceeding to this stage."))
        self.state = 'reject_ceo_review'

    def write(self, values):
        if 'state' in values:
            current_state = self.state
            new_state = values.get('state')

            # Allow transition only if it's a valid state change for the current user
            if current_state == 'draft' and self.env.user.has_group('base.group_user') and new_state == 'submitted':
                # Initiator can submit, but not proceed to other states directly
                pass
            elif current_state == 'submitted' and self.env.user.has_group('complaint_handling.group_legal_servicedepartment') and new_state == 'legal_reviewed':
                # Legal Service can only review after submission
                pass
            elif current_state == 'legal_reviewed' and self.env.user.has_group('base.group_user') and new_state in ['accept_legal_review', 'reject_legal_review']:
                # Initiator can accept or reject legal review
                pass
            elif current_state == 'reject_legal_review' and self.env.user.has_group('complaint_handling.group_ceo') and new_state == 'ceo_reviewed':
                # CEO can review only after legal review
                pass
            elif current_state == 'ceo_reviewed' and self.env.user.has_group('base.group_user') and new_state in ['accept_ceo_review', 'reject_ceo_review']:
                # Initiator can accept or reject CEO review
                pass
            else:
                raise ValidationError(_("You do not have the access rights to perform this action."))

        return super(EmployeeComplaint, self).write(values)
    
    def action_save_complaint(self):
        for record in self:
            # Saving the record
            record.write({
                'name': record.name,
                'employee_id': record.employee_id.id,
                'issue_type': record.issue_type,
                'description': record.description,
                'documents': [(6, 0, record.documents.ids)],
                'decision_by_legalservice': record.decision_by_legalservice,
                'decision_by_ceo': record.decision_by_ceo,
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Your complaint has been successfully saved!',
                'type': 'success',
                'sticky': False,  # It will disappear after a few seconds
            }
        }
    