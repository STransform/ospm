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
    documents = fields.Many2many('ir.attachment', string='Attachments',relation='employee_complaint_for_complainer_rel', help="Attach documents related to the complaint")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('legal_reviewed', 'Legal Reviewed'),
        ('accept_legal_review', 'Accepted,Legal Review'),
        ('reject_legal_review', 'Rejected,Legal Review'),
        ('ceo_reviewed', 'CEO Reviewed'),
        ('accept_ceo_review', 'Accepted,CEO Review'),
        ('reject_ceo_review', 'Rejected,CEO Reviewed')
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
    documents_by_legal_service = fields.Many2many('ir.attachment',relation='employee_complaint_for_legal_service_rel', string='Documents by legal service department', help="Attach documents by legal service decision")

    
    is_creator = fields.Boolean(string="Is Creator", compute="_compute_is_creator", store=False)
    is_ceo = fields.Boolean(string="Is CEO", compute="_compute_is_ceo", store=False)
    is_legal_service = fields.Boolean(string="Is Legal Service", compute="_compute_is_legal_service", store=False)


    @api.model
    def _compute_is_creator(self):
        if self.employee_id:
            self.is_creator = self.employee_id.user_id.id == self.env.user.id
    
    @api.model
    def _compute_is_ceo(self):
        self.is_ceo = self.env.user.has_group("user_group.group_ceo")

    @api.model
    def _compute_is_legal_service(self):
        self.is_legal_service = self.env.user.has_group("user_group.group_legal_servicedepartment")

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
    @api.model
    def send_notification(self, message, user, title, model,res_id):
        self.env['custom.notification'].create({
            'title': title,
            'message': message,
            'user_id': user.id,
            'action_model': model,
            'action_res_id': res_id
        })

    def action_submit(self):
        self._check_access('base.group_user')  # Only initiator (regular users)
        if self.state != 'draft':
            raise ValidationError(_("Only complaints in draft state can be submitted to Legal Service."))
        self.state = 'submitted'
        
        # Prepare the message
        message = f"This is my complaint details submitted to you,for review!"
        # Get the users in the group "group_department_approval"
        legal_service_group = self.env.ref('user_group.group_legal_servicedepartment', raise_if_not_found=False)
        if legal_service_group:
            for user in legal_service_group.users:
                # Send notification to each user in the department approval group
                self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
                user.notify_warning(message=message, title=self._description)
        
        return {
                'type': 'ir.actions.act_window',
                'name': 'Employee Complaints',
                'res_model': 'employee.complaint',
                'view_mode': 'tree,form',
                'view_id': False,
                'views': [(False, 'tree'), (False, 'form')],
                'target': 'current',
                'context': {},
                'domain': [],  
                'res_id': False,     
            
                'params': {
                    'title': 'Success',
                    'message': 'Your decision has been successfully saved!',
                    'type': 'success',
                    'sticky': False,  
                }
        }
        

    def action_legal_review(self):
        self._check_access('user_group.group_legal_servicedepartment')  # Legal department group
        if self.state != 'submitted':
            raise ValidationError(_("Only complaints in submitted state can be legal reviewed."))
        self.state = 'legal_reviewed'
        # Prepare the message
        message = "Complaint details have been reviewed. Please verify if they are satisfactory."
        
        # Send notification to the complaint initiator
        if self.employee_id and self.employee_id.user_id:
            self.send_notification(message=message, user=self.employee_id.user_id, title=self._description, model=self._name, res_id=self.id)
            self.employee_id.user_id.notify_warning(message=message, title=self._description)
            

    def action_accept_legal_review(self):
        self._check_access('base.group_user')  # Only initiator (regular users)
        if self.state != 'legal_reviewed':
            raise ValidationError(_("Legal reviewed must be done first!"))
        self.state = 'accept_legal_review'
        # Prepare the message
        message = f"I've accepted your response.Thank you very much!."
        # Get the users in the group "group_department_approval"
        legal_service_group = self.env.ref('user_group.group_legal_servicedepartment', raise_if_not_found=False)
        if legal_service_group:
            for user in legal_service_group.users:
                # Send notification to each user in the department approval group
                self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
                user.notify_warning(message=message, title=self._description)
        
        return {
                'type': 'ir.actions.act_window',
                'name': 'Employee Complaints',
                'res_model': 'employee.complaint',
                'view_mode': 'tree,form',
                'view_id': False,
                'views': [(False, 'tree'), (False, 'form')],
                'target': 'current',
                'context': {},
                'domain': [],  
                'res_id': False,     
            
                'params': {
                    'title': 'Success',
                    'message': 'Your decision has been successfully saved!',
                    'type': 'success',
                    'sticky': False,  
                }
        }
        

    def action_reject_legal_review(self):
        self._check_access('base.group_user')  # Only initiator (regular users)
        if self.state != 'legal_reviewed':
            raise ValidationError(_("Legal reviewed must be done first!"))
        self.state = 'reject_legal_review'
        # Prepare the message
        message = f"Legal service review not satisfactory, so I escalated the case to you for further review and better response."
        # Get the users in the group "group_department_approval"
        ceo_group = self.env.ref('user_group.group_ceo', raise_if_not_found=False)
        if ceo_group:
            for user in ceo_group.users:
                # Send notification to each user in the department approval group
                self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
                user.notify_warning(message=message, title=self._description)
        
        return {
                'type': 'ir.actions.act_window',
                'name': 'Employee Complaints',
                'res_model': 'employee.complaint',
                'view_mode': 'tree,form',
                'view_id': False,
                'views': [(False, 'tree'), (False, 'form')],
                'target': 'current',
                'context': {},
                'domain': [],  
                'res_id': False,     
            
                'params': {
                    'title': 'Success',
                    'message': 'Your decision has been successfully saved!',
                    'type': 'success',
                    'sticky': False,  
                }
        }
        

    def action_ceo_review(self):
        self._check_access('user_group.group_ceo')  # CEO group
        if self.state != 'legal_reviewed' and self.state not in ['accept_legal_review', 'reject_legal_review']:
            raise ValidationError(_("Legal reviewed must be done first!"))
        self.state = 'ceo_reviewed'
        
        # Prepare the message
        message = "Complaint details have been reviewed by the CEO. Please verify if they are satisfactory."
        
        # Send notification to the complaint initiator
        if self.employee_id and self.employee_id.user_id:
            self.send_notification(message=message, user=self.employee_id.user_id, title=self._description, model=self._name, res_id=self.id)
            self.employee_id.user_id.notify_warning(message=message, title=self._description)
        

    def action_accept_ceo_review(self):
        self._check_access('base.group_user')  # Only initiator (regular users)
        if self.state != 'ceo_reviewed':
            raise ValidationError(_("Legal and CEO reviews must be completed before proceeding to this stage."))
        self.state = 'accept_ceo_review'
          # Prepare the message
        message = f"I've accepted your response.I want to thank you."
        # Get the users in the group "group_department_approval"
        ceo_group = self.env.ref('user_group.group_ceo', raise_if_not_found=False)
        if ceo_group:
            for user in ceo_group.users:
                # Send notification to each user in the department approval group
                self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
                user.notify_warning(message=message, title=self._description)
        
        return {
                'type': 'ir.actions.act_window',
                'name': 'Employee Complaints',
                'res_model': 'employee.complaint',
                'view_mode': 'tree,form',
                'view_id': False,
                'views': [(False, 'tree'), (False, 'form')],
                'target': 'current',
                'context': {},
                'domain': [],  
                'res_id': False,     
            
                'params': {
                    'title': 'Success',
                    'message': 'Your decision has been successfully saved!',
                    'type': 'success',
                    'sticky': False,  
                }
        }
        


    def action_reject_ceo_review(self):
        self._check_access('base.group_user')  # Only initiator (regular users)
        if self.state != 'ceo_reviewed':
            raise ValidationError(_("Legal and CEO reviews must be completed before proceeding to this stage."))
        self.state = 'reject_ceo_review'
        # Prepare the message
        message = f"CEO review is not satisfactory,I want to take the case to the court!."
        # Get the users in the group "group_department_approval"
        ceo_group = self.env.ref('base.group_user', raise_if_not_found=False)
        if ceo_group:
            for user in ceo_group.users:
                # Send notification to each user in the department approval group
                self.send_notification(message=message, user=user, title=self._description, model=self._name, res_id=self.id)
                user.notify_warning(message=message, title=self._description)
        
        return {
                'type': 'ir.actions.act_window',
                'name': 'Employee Complaints',
                'res_model': 'employee.complaint',
                'view_mode': 'tree,form',
                'view_id': False,
                'views': [(False, 'tree'), (False, 'form')],
                'target': 'current',
                'context': {},
                'domain': [],  
                'res_id': False,     
            
                'params': {
                    'title': 'Success',
                    'message': 'Your decision has been successfully saved!',
                    'type': 'success',
                    'sticky': False,  
                }
        }
        

    def write(self, values):
        if 'state' in values:
            current_state = self.state
            new_state = values.get('state')

            # Allow transition only if it's a valid state change for the current user
            if current_state == 'draft' and self.env.user.has_group('base.group_user') and new_state == 'submitted':
                # Initiator can submit, but not proceed to other states directly
                pass
            elif current_state == 'submitted' and self.env.user.has_group('user_group.group_legal_servicedepartment') and new_state == 'legal_reviewed':
                # Legal Service can only review after submission
                pass
            elif current_state == 'legal_reviewed' and self.env.user.has_group('base.group_user') and new_state in ['accept_legal_review', 'reject_legal_review']:
                # Initiator can accept or reject legal review
                pass
            elif current_state == 'reject_legal_review' and self.env.user.has_group('user_group.group_ceo') and new_state == 'ceo_reviewed':
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
                'type': 'ir.actions.act_window',
                'name': 'Employee Complaints',
                'res_model': 'employee.complaint',
                'view_mode': 'tree,form',
                'view_id': False,
                'views': [(False, 'tree'), (False, 'form')],
                'target': 'current',
                'context': {},
                'domain': [],  
                'res_id': False,     
            
                'params': {
                    'title': 'Success',
                    'message': 'Your decision has been successfully saved!',
                    'type': 'success',
                    'sticky': False,  
                }
        }
    