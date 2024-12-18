from odoo import models, fields, api,_
from odoo.exceptions import  ValidationError
class DisciplineCase(models.Model):
    _name = 'employee.discipline.case'
    _description = 'Employee Discipline Case Management'
    _order = 'create_date desc'
    # Existing fields
    name = fields.Char('Case Reference', required=True, copy=False)
    accuser_id = fields.Many2one('res.users', string='Accuser',readonly=True, default=lambda self: self.env.user)
    accused_employee_id = fields.Many2one('res.users', string='Accused', required=True)
    case_description = fields.Text('Case Description', required=True)
    case_revision = fields.Text('Revision', required=True, default='revised')
    discipline_type = fields.Selection([('misconduct', 'Misconduct'), ('poor_performance', 'Poor Performance'),
                                        ('violence', 'Violence'), ('harassment', 'Harassment'),
                                        ('theft', 'Theft'), ('other', 'Other')], 
                                       string='Discipline Type', required=True, default='misconduct')
    penalty_type = fields.Selection([
        ('salary', 'Salary deduction'),
        ('warning', 'Warning'),
        ('dismiss', 'Dismissal'),
        ('demotion', 'Demotion'),
    ], string='Penalty Type',default='salary')

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
    documents = fields.Many2many('ir.attachment', relation='employee_discipline_case_documents_rel', string='Attachments', help="Attach documents related to discipline case")
    accused_response = fields.Text('Accused Response', help="Response from the accused (only for HR to fill)")
    witness_by_accused = fields.Many2many('res.users', string='Witnesses by Accused', help="Witnesses selected by the committee for the case")
    reason_for_revision = fields.Text('Reason for Revision', help="Reason revision (only for CEO to fill)")
    

    state = fields.Selection([
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('resolved', 'Resolved by Hr'),
            ('escalate_to_committee', 'Escalated to Committee'),
            ('escalate_to_ceo', 'Escalated to ceo'),
            ('reviewed', 'Reviewed'),
            ('approve', 'Approved'),
            ('reject', 'Returned')
        ], default='draft', string='Status', tracking=True)

    approve_after = fields.Boolean(string="Approved After", default=False )
    rejected_more = fields.Boolean(string="Rejected more", default=False)
    is_creator = fields.Boolean(string="Is Creator", compute="_compute_is_creator", store=False)
    is_hr = fields.Boolean(string="Is Hr", compute="_compute_is_hr", store=False)
    is_committee = fields.Boolean(string="Is Committee", compute="_compute_is_committee", store=False)
    is_ceo = fields.Boolean(string="Is CEO", compute="_compute_is_ceo", store=False)
    reason_for_revision_is_visible = fields.Boolean(string="Reason Visibility", compute="_compute_reason_for_revision_is_visible", store=False)
    case_revision_is_visible = fields.Boolean(string="Reason Visibility", compute="_compute_case_revision_is_visible", store=False)
    documents_for_committee = fields.Many2many('ir.attachment',relation='employee_discipline_case_documents_for_committee_rel', string='Documents by committee', help="Attach documents by committee decision")


    @api.model
    def _compute_reason_for_revision_is_visible(self):
        if self.env.user.has_group("user_group.group_ceo"):
            self.reason_for_revision_is_visible = self.state in ['escalate_to_ceo','reject','reviewed'] or self.approve_after
        else:
            self.reason_for_revision_is_visible = self.state in ['reject','reviewed'] or self.approve_after

    @api.model
    def _compute_case_revision_is_visible(self):
        if self.env.user.has_group('user_group.group_discipline_committee'):
            self.case_revision_is_visible = self.state in ['reject','reviewed'] or self.approve_after
        else:
            self.case_revision_is_visible = self.state == 'reviewed' or self.approve_after or self.rejected_more

    @api.model
    def _compute_is_creator(self):
        if self.accuser_id:
            self.is_creator = self.accuser_id.user_id.id == self.env.user.id
    
    @api.model
    def _compute_is_hr(self):
        self.is_hr = self.env.user.has_group("user_group.group_hr_director")

    @api.model
    def _compute_is_committee(self):
        self.is_committee = self.env.user.has_group("user_group.group_discipline_committee")
    @api.model
    def _compute_is_ceo(self):
        self.is_ceo = self.env.user.has_group("user_group.group_ceo")
    approve_button_visible = fields.Boolean(compute='_compute_approve_button', store=True)
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
    
    def write(self, values):
        if 'state' in values:
            current_state = self.state
            new_state = values['state']
            user = self.env.user

            # State transition rules
            if current_state == 'draft' and new_state == 'submitted' and user.has_group('base.group_user'):
                pass
            elif current_state == 'submitted' and new_state == 'resolved' and user.has_group('user_group.group_hr_director'):
                pass
            elif current_state == 'submitted' and new_state == 'escalate_to_committee' and user.has_group('user_group.group_hr_director'):
                pass
            elif current_state == 'escalate_to_committee' and new_state == 'escalate_to_ceo' and user.has_group('user_group.group_discipline_committee'):
                pass
            elif current_state == 'escalate_to_ceo' and new_state == 'approve' and user.has_group('user_group.group_ceo'):
                pass
            elif current_state == 'escalate_to_ceo' and new_state == 'reject' and user.has_group('user_group.group_ceo'):
                pass
            elif current_state == 'reject' and new_state == 'reviewed' and user.has_group('user_group.group_discipline_committee'):
                pass
            elif current_state == 'reviewed' and (new_state == 'approve' or new_state == 'reject') and user.has_group('user_group.group_ceo'):
                pass
            else:
                raise ValidationError(_("You do not have the rights to perform this state transition or the transition is invalid."))

        return super(DisciplineCase, self).write(values)
    
    # Action Buttons
    def _check_access(self, allowed_groups):
        """Check if the current user belongs to one of the allowed groups."""
        if not self.env.user.has_group(allowed_groups):
            raise ValidationError(_("You do not have the access rights to perform this action."))

    def action_submit(self):
        self._check_access('base.group_user')  # Only users in base.group_user can submit
        if self.state != 'draft':
            raise ValidationError(_("Only cases in the 'Draft' state can be submitted."))
        self.write({'state': 'submitted'})
         # Prepare the message
        message = f"This case has been submitted to you!,Pls kindly resolve it ASAP!"
        # Get the users in the group "group_department_approval"
        hr_department_group = self.env.ref('user_group.group_hr_director', raise_if_not_found=False)
        if hr_department_group:
            for user in hr_department_group.users:
                # Send notification to each user in the department approval group
                self.send_notification(message=message, user=user, title=self._description)
                user.notify_warning(message=message, title=self._description)
        
        return {
                'type': 'ir.actions.act_window',
                'name': 'Discipline case',
                'res_model': 'employee.discipline.case',
                'view_mode': 'tree,form', 
                'view_id': False,     
                'views': [(False, 'tree'), (False, 'form')],  
                'target': 'current',
                'context': {},      
                'domain': [],            
                'res_id': False,   
                'params': {
                    'title': 'Success',
                    'message': ' I have successfully submitted the case!',
                    'type': 'success',
                    'sticky': False,  # It will disappear after a few seconds
                }
            }
        

    def action_resolve(self):
        self._check_access('user_group.group_hr_director')  # Only HR can resolve
        if self.state != 'submitted':
            raise ValidationError(_("Only cases in the 'Submitted' state can be resolved."))
        self.write({'state': 'resolved'})
        # Notification Messages
        accuser_message = "Your discipline case has been resolved by HR. Please review the outcome."
        accused_message = "A discipline case involving you has been resolved by HR. Please review the outcome."

        # Notify the accuser
        if self.accuser_id:
            self.send_notification(message=accuser_message, user=self.accuser_id, title=self._description)
            self.accuser_id.notify_warning(message=accuser_message, title=self._description)

        # Notify the accused
        if self.accused_employee_id:
            self.send_notification(message=accused_message, user=self.accused_employee_id, title=self._description)
            self.accused_employee_id.notify_warning(message=accused_message, title=self._description)
        
        return {
                'type': 'ir.actions.act_window',
                'name': 'Discipline case',
                'res_model': 'employee.discipline.case',
                'view_mode': 'tree,form', 
                'view_id': False,     
                'views': [(False, 'tree'), (False, 'form')],  
                'target': 'current',
                'context': {},      
                'domain': [],            
                'res_id': False,   
                'params': {
                    'title': 'Success',
                    'message': ' I have successfully resolved the case!',
                    'type': 'success',
                    'sticky': False,  # It will disappear after a few seconds
                }
            }

    def action_escalate_to_committee(self):
        self._check_access('user_group.group_hr_director')  # Only HR can escalate to committee
        if self.state != 'submitted':
            raise ValidationError(_("Only cases in the 'Submitted' state can be escalated to the committee."))
        self.write({'state': 'escalate_to_committee'})
         # Prepare the message
        message = f"This case has been scalated to you!,Pls kindly resolve it ASAP!"
        # Get the users in the group "group_department_approval"
        committee_group = self.env.ref('user_group.group_discipline_committee', raise_if_not_found=False)
        if committee_group:
            for user in committee_group.users:
                # Send notification to each user in the department approval group
                self.send_notification(message=message, user=user, title=self._description)
                user.notify_warning(message=message, title=self._description)
        
        return {
                'type': 'ir.actions.act_window',
                'name': 'Discipline case',
                'res_model': 'employee.discipline.case',
                'view_mode': 'tree,form', 
                'view_id': False,     
                'views': [(False, 'tree'), (False, 'form')],  
                'target': 'current',
                'context': {},      
                'domain': [],            
                'res_id': False,   
                'params': {
                    'title': 'Success',
                    'message': ' I have successfully escalated the case to committee!',
                    'type': 'success',
                    'sticky': False,  # It will disappear after a few seconds
                }
            }
        

    def action_escalate_to_ceo(self):
        self._check_access('user_group.group_discipline_committee')  # Only committee can escalate to CEO
        if self.state != 'escalate_to_committee':
            raise ValidationError(_("Only cases in the 'Escalate to Committee' state can be escalated to the CEO."))
        self.write({'state': 'escalate_to_ceo'})
         # Prepare the message
        message = f"This case has been scalated to you!,Pls kindly resolve it ASAP!"
        # Get the users in the group "group_department_approval"
        ceo = self.env.ref('user_group.group_ceo', raise_if_not_found=False)
        if ceo:
            for user in ceo.users:
                # Send notification to each user in the department approval group
                self.send_notification(message=message, user=user, title=self._description)
                user.notify_warning(message=message, title=self._description)

        return {
                'type': 'ir.actions.act_window',
                'name': 'Discipline case',
                'res_model': 'employee.discipline.case',
                'view_mode': 'tree,form', 
                'view_id': False,     
                'views': [(False, 'tree'), (False, 'form')],  
                'target': 'current',
                'context': {},      
                'domain': [],            
                'res_id': False,   
                'params': {
                    'title': 'Success',
                    'message': ' I have successfully escalated the case to ceo',
                    'type': 'success',
                    'sticky': False,  # It will disappear after a few seconds
                }
            }
        
        

    def action_approve(self):
        self._check_access('user_group.group_ceo')  # Only CEO can approve
        if self.state not in ['escalate_to_ceo','reviewed']:
            raise ValidationError(_("Only cases in the 'Escalate to CEO' or 'Reviewed' state can be approved."))
        if self.state == 'reviewed':
            self.write({'approve_after': True})
        self.write({'state': 'approve'})

         # Prepare the message
        message = f"This case has been approved!,Pls kindly check it and take your action!"
        # Get the users in the group "group_department_approval"
        hr = self.env.ref('user_group.group_hr_director', raise_if_not_found=False)
        if hr:
            for user in hr.users:
                # Send notification to each user in the department approval group
                self.send_notification(message=message, user=user, title=self._description)
                user.notify_warning(message=message, title=self._description)
        
        return {
                'type': 'ir.actions.act_window',
                'name': 'Discipline case',
                'res_model': 'employee.discipline.case',
                'view_mode': 'tree,form', 
                'view_id': False,     
                'views': [(False, 'tree'), (False, 'form')],  
                'target': 'current',
                'context': {},      
                'domain': [],            
                'res_id': False,   
                'params': {
                    'title': 'Success',
                    'message': ' I have successfully approved!',
                    'type': 'success',
                    'sticky': False,  # It will disappear after a few seconds
                }
            }
        
        
        


    def action_reject(self):
        self._check_access('user_group.group_ceo')  # Only CEO can reject
        if self.state not in ["escalate_to_ceo","reviewed"]:
            raise ValidationError(_("Only cases in the 'Escalate to CEO' state can be rejected."))
        if not self.reason_for_revision:
            raise ValidationError("You need Reason to reject the Request")
        if self.state == 'reviewed':
            self.write({'rejected_more':True})
        self.write({'state': 'reject'})
          # Prepare the message
        message = f"This case has been returned to you!,Pls kindly review it and send it back to me ASAP!"
        # Get the users in the group "group_department_approval"
        returned_to_committee = self.env.ref('user_group.group_discipline_committee', raise_if_not_found=False)
        if returned_to_committee:
            for user in returned_to_committee.users:
                # Send notification to each user in the department approval group
                self.send_notification(message=message, user=user, title=self._description)
                user.notify_warning(message=message, title=self._description)
        
        return {
                'type': 'ir.actions.act_window',
                'name': 'Discipline case',
                'res_model': 'employee.discipline.case',
                'view_mode': 'tree,form', 
                'view_id': False,     
                'views': [(False, 'tree'), (False, 'form')],  
                'target': 'current',
                'context': {},      
                'domain': [],            
                'res_id': False,   
                'params': {
                    'title': 'Success',
                    'message': ' I have successfully returned the case!',
                    'type': 'success',
                    'sticky': False,  # It will disappear after a few seconds
                }
            }

    def action_review(self):
        self._check_access('user_group.group_discipline_committee')  # Only committee can review
        if self.state != 'reject':
            raise ValidationError(_("Only cases in the 'Rejected' state can be reviewed."))
        self.write({'state': 'reviewed'})
         # Prepare the message
        message = f"I reviewed the case and sent it back to you,Pls kindly review it and approve it!"
        # Get the users in the group "group_department_approval"
        to_ceo = self.env.ref('user_group.group_ceo', raise_if_not_found=False)
        if to_ceo:
            for user in to_ceo.users:
                # Send notification to each user in the department approval group
                self.send_notification(message=message, user=user, title=self._description)
                user.notify_warning(message=message, title=self._description)
        
        return {
                'type': 'ir.actions.act_window',
                'name': 'Discipline case',
                'res_model': 'employee.discipline.case',
                'view_mode': 'tree,form', 
                'view_id': False,     
                'views': [(False, 'tree'), (False, 'form')],  
                'target': 'current',
                'context': {},      
                'domain': [],            
                'res_id': False,   
                'params': {
                    'title': 'Success',
                    'message': ' I have successfully reviewed!',
                    'type': 'success',
                    'sticky': False,  # It will disappear after a few seconds
                }
            }
        

    
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
                'type': 'ir.actions.act_window',
                'name': 'Discipline case',
                'res_model': 'employee.discipline.case',
                'view_mode': 'tree,form', 
                'view_id': False,     
                'views': [(False, 'tree'), (False, 'form')],  
                'target': 'current',
                'context': {},      
                'domain': [],            
                'res_id': False,   
                'params': {
                    'title': 'Success',
                    'message': 'You have successfully saved the case!',
                    'type': 'success',
                    'sticky': False,  # It will disappear after a few seconds
                }
            }