from odoo import models, fields, api
from odoo.exceptions import  ValidationError
class DisciplineCase(models.Model):
    _name = 'employee.discipline.case'
    _description = 'Employee Discipline Case Management'
    _order = 'create_date desc'
    # Existing fields
    name = fields.Char('Case Reference', required=True, copy=False)
    accuser_id = fields.Many2one('res.users', string='Accuser', default=lambda self: self.env.user)
    accused_employee_id = fields.Many2one('res.users', string='Accused', required=True)
    case_description = fields.Text('Case Description', required=True)
    
    discipline_type = fields.Selection([('misconduct', 'Misconduct'), ('poor_performance', 'Poor Performance'),
                                        ('violence', 'Violence'), ('harassment', 'Harassment'),
                                        ('theft', 'Theft'), ('other', 'Other')], 
                                       string='Discipline Type', required=True, default='misconduct')
    penalty_type = fields.Selection([
        ('salary', 'Salary deduction'),
        ('warning', 'Warning'),
        ('dismiss', 'Dismissal'),
        ('demotion', 'Demotion'),
    ], string='Discipline Type', required=True, default='salary')

    hr_decision = fields.Selection([('resolve', 'Resolved by HR'), 
                                    ('escalate_to_committee', 'Escalate to Committee')],
                                   string='HR Decision')
    
    committee_decision = fields.Selection([('escalate_to_ceo', 'Escalate to CEO'), 
                                           ('reviewed', 'Reviewed')], 
                                          string='Committee Decision')
    
    ceo_decision = fields.Selection([('approved', 'Approved'), ('rejected', 'Returned to Committee'),
                                     ('reviewed', 'Reviewed')], string='CEO Decision')
    
    assigned_to_committee = fields.Many2one('res.users', string='Assigned Committee Member', readonly=True)
    assigned_to_ceo = fields.Many2one('res.users', string='Assigned CEO', readonly=True)
    documents = fields.Many2many('ir.attachment', string='Attachments', help="Attach documents related to discipline case")
    accused_response = fields.Text('Accused Response', help="Response from the accused (only for HR to fill)")
    witness_by_accused = fields.Many2many('res.users', string='Witnesses by Accused', help="Witnesses selected by the committee for the case")
    reason_for_revision = fields.Text('Reason for Revision', help="Reason revision (only for CEO to fill)")
    
    # New field for case status
    case_status = fields.Char('Case Status', compute='_compute_case_status', store=True)
    
    @api.depends('hr_decision', 'committee_decision', 'ceo_decision')
    def _compute_case_status(self):
        """Compute the overall status of the discipline case."""
        for record in self:
            # Ensure that case_status is set to 'Pending' when no decisions have been made yet.
            if not record.hr_decision and not record.committee_decision and not record.ceo_decision:
                record.case_status = 'Pending'
            elif record.hr_decision == 'resolve':
                record.case_status = 'Resolved by HR'
            elif record.ceo_decision == 'approved':
                record.case_status = 'Approved by CEO'
            elif record.ceo_decision == 'rejected':
                record.case_status = 'Returned from CEO'
            elif record.committee_decision == 'escalate_to_ceo':
                record.case_status = 'Escalated to CEO'
            elif record.committee_decision == 'reviewed':
                record.case_status = 'Reviewed by Committee'
            elif record.hr_decision == 'escalate_to_committee':
                record.case_status = 'Escalated to Committee'
            else:
                record.case_status = 'Pending'

    @api.onchange('hr_decision')
    def _onchange_hr_decision(self):
        """Set the case status to 'Resolved by HR' immediately when HR selects 'Resolved'."""
        if self.hr_decision == 'resolve':
            self.case_status = 'Resolved by HR'
    @api.model
    def check_user_group(self):
        return self.env.user.has_group('hr_discipline_case2.group_discipline_committee')

    def action_return_from_ceo(self):
        """Set the state to 'Returned from CEO' when the case is returned by the CEO."""
        for record in self:
            if record.ceo_decision == 'rejected':
                record.committee_decision = 'return_from_ceo'
                record.case_status = 'Returned from CEO'

    def action_escalate_to_ceo(self):
        """Escalate the case to the CEO from the committee."""
        for record in self:
            if record.committee_decision == 'reviewed':  # Ensure the case is reviewed
                # Set the case to escalate to CEO
                record.committee_decision = 'escalate_to_ceo'
                record.case_status = 'Escalated to CEO'
                
                # When the case is escalated to CEO, also set it as 'Reviewed' for the CEO
                record.ceo_decision = 'reviewed'
                
                # You may also want to assign the case to a CEO user if not already assigned
                if not record.assigned_to_ceo:
                    record.assigned_to_ceo = self.env.user.id
# Add SQL constraint for unique name
    _sql_constraints = [
        ('unique_case_reference', 'unique(name)', 'The Case Reference must be unique.')
    ]
    def action_save_discipline_case(self):
            for record in self:
                # Saving the record 
                record.write({
                    'name': record.name,
                    'accuser_id': record.accuser_id.id,
                    'accused_employee_id': record.accused_employee_id.id,
                    'case_description': record.case_description,
                    'discipline_type': record.discipline_type,
                    'penalty_type': record.penalty_type,
                    'hr_decision': record.hr_decision,
                    'committee_decision': record.committee_decision,
                    'ceo_decision': record.ceo_decision,
                    'assigned_to_committee': record.assigned_to_committee.id,
                    'assigned_to_ceo': record.assigned_to_ceo.id,
                    'documents': [(6, 0, record.documents.ids)],
                    'accused_response': record.accused_response,
                    'witness_by_accused': [(6, 0, record.witness_by_accused.ids)],
                    'reason_for_revision': record.reason_for_revision,
                })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'You have successfully saved the case!',
                    'type': 'success',
                    'sticky': False,  # It will disappear after a few seconds
                }
            }