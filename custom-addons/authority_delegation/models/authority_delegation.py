from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from babel.dates import format_date

class AuthorityDeligation(models.Model):
    _name = 'authority.delegation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Authority Delegation"
    _rec_name = "delegator_id"

    delegator_id = fields.Many2one("hr.employee", string="Delegator", required=True, default=lambda self:self.env.user.employee_id)
    delegatee_id = fields.Many2one("hr.employee", string="Delegatee", required=True)
    delegator_user = fields.Many2one("res.users", string="Delegator User", compute="_compute_delegator_user", store=True)
    delegatee_user = fields.Many2one("res.users", string="Delegatee User", compute="_compute_delegatee_user", store=True)
    delegation_position = fields.Char(string="Delegated Position", compute="_compute_delegator_user")
    delegation_start_date = fields.Date(string="Start Date", required=True)
    delegation_end_date = fields.Date(string="End Date", required=True)
    status = fields.Selection([
        ("draft", "Draft"), 
        ("submitted", "Submitted"), 
        ("accepted_by_delegatee", "Accepted By Delegatee"),
        ("rejected_by_delegatee", "Rejected By Delegatee"),
        ("approved", "Approved"), 
        ("rejected", "Rejected")
        ],
        string="Status",
        default="draft",
        track_visibility="onchange",
    )
    delegatee_response = fields.Text(string="Delegatee Reason")
    Hr_response = fields.Text(string="HR Reason")
    reason = fields.Text(string="Reason for Delegation", required=True)
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this training session."
    )

    is_delegator = fields.Boolean(string="Is Delegator", compute="_compute_is_delegator", store=False)
    is_delegatee = fields.Boolean(string="Is Delegatee", compute="_compute_is_delegatee", store=False)
    is_hr_director = fields.Boolean(string="Is HR Director", compute="_compute_is_hr_director", store=False)

    # Format the date to a human-readable format
    def _format_date(self, date):
        if date:
            return format_date(date, format="long", locale=self.env.user.lang or "en_US")
        return ""

    @api.model
    def _compute_is_delegator(self):
        for record in self:
            record.is_delegator = record.delegator_id.user_id == self.env.user
    
    @api.model
    def _compute_is_delegatee(self):
        for record in self:
            record.is_delegatee = record.delegatee_id.user_id == self.env.user
    
    @api.model
    def _compute_is_hr_director(self):
        for record in self:
            record.is_hr_director = self.env.user.has_group("user_group.group_hr_director")
    

    @api.depends("delegator_id")
    def _compute_delegator_user(self):
        for record in self:
            if not record._origin and record.delegator_id and not record.delegator_id.user_id:
                raise ValidationError(_("The selected delegator does not have a user. Please contact the administrator."))
            # if not record._origin and record.delegator_id and not record.delegator_id.job_title:
            #     raise ValidationError(_("The selected delegator does not have a Job Title. Please contact the administrator."))
            record.delegator_user = record.delegator_id.user_id
            record.delegation_position = record.delegator_id.job_title if record.delegator_id.job_title else "N/A"
    
    @api.depends("delegatee_id")
    def _compute_delegatee_user(self):
        for record in self:
            if not record._origin and record.delegatee_id:
                if not record.delegatee_id.user_id:
                    raise ValidationError(_("The selected delegatee does not have a user. Please contact the administrator."))
                if record.delegatee_id.user_id == record.delegator_id.user_id:
                    raise ValidationError(_("The selected delegatee cannot be the same as the delegator. Please select a different delegatee."))
            record.delegatee_user = record.delegatee_id.user_id

    ## date Validation
    @api.onchange('delegation_start_date','delegation_end_date')
    def validate_date(self):
        if self.delegation_start_date and self.delegation_start_date <= fields.Date.today():
            raise ValidationError(_("Start date cannot be in the past or today. Please select a future date.")) 
        if self.delegation_end_date and self.delegation_end_date <= fields.Date.today():
            raise ValidationError(_("End date cannot be in the past or today. please select a future date."))
        if self.delegation_end_date and self.delegation_start_date and self.delegation_start_date >= self.delegation_end_date:
            raise ValidationError(_("Start Date must be before End Date."))
    
    
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

    ### submit action for Authority Delegation
    def action_submit(self):
        if not self.is_delegator:
            raise ValidationError(_("You are not allowed to submit this request."))
        if self.status != "draft":
            raise ValidationError(_("You are not allowed to submit this request."))
    
        ## notify the delegatee
        self.status = "submitted"
        hr_director = self.env.ref("user_group.group_hr_director").users
        
        title = "Request for Authority delegation"
        message = f"{self.delegator_id.name} has requested you to accept  delegation for the position of {self.delegation_position} from {self._format_date(self.delegation_start_date)} to {self._format_date(self.delegation_end_date)}."
        hr_message = f"{self.delegator_id.name} has requested for delegation for the position of {self.delegation_position} from {self._format_date(self.delegation_start_date)} to {self._format_date(self.delegation_end_date)}."
        self.send_notification(message=message, user=self.delegatee_user, title=title, model=self._name, res_id=self.id)
        for user in hr_director:
            self.send_notification(message=hr_message, user=user, title=title, model=self._name, res_id=self.id)
            user.notify_success(title=title, message=hr_message)
        self.delegatee_user.notify_success(title=title,message=message)
        self.env.user.notify_success("Request Submitted")
        return {  
            'type': 'ir.actions.act_window',
            'name': 'Request Delegation',
            'res_model': self._name,
            'view_mode': 'tree,form',
            'target': 'current',
        }
        
    
    ### accept deligation action for Authority Delegation
    def action_accept_delegation(self):
        if not self.is_delegatee:
            raise ValidationError(_("You are not allowed to accept this request."))
        if self.status != "submitted":
            raise ValidationError(_("You are not allowed to accept this request."))
        self.status = "accepted_by_delegatee"
        hr_director = self.env.ref("user_group.group_hr_director").users

        title = "Authority delegation Acceptance"
        message = f"{self.delegatee_id.name} has accepted your request for delegation for the position of {self.delegation_position} from {self._format_date(self.delegation_start_date)} to {self._format_date(self.delegation_end_date)}."
        hr_message = f"{self.delegatee_id.name} has accepted the request for delegation for the position of {self.delegation_position} from {self._format_date(self.delegation_start_date)} to {self._format_date(self.delegation_end_date)}."
        self.send_notification(message=message, user=self.delegator_user, title=title, model=self._name, res_id=self.id)
        for user in hr_director:
            self.send_notification(message=hr_message, user=user, title=title, model=self._name, res_id=self.id)
            user.notify_success(title=title, message=hr_message)
        self.delegator_user.notify_success(title=title,message=message)
        self.env.user.notify_success("Request Accepted")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Delegation',
            'res_model': self._name,
            'view_mode': 'tree,form',
            'target': 'current',
        }

    ### Reject deligation action for Authority Delegation
    def action_refuse_delegation(self):
        if not self.is_delegatee:
            raise ValidationError(_("You are not allowed to reject this request."))
        if self.status != "submitted":
            raise ValidationError(_("You are not allowed to reject this request."))
        if not self.delegatee_response:
            raise ValidationError(_("Please provide a reason for rejecting the request to the delegator."))
        self.status = "rejected_by_delegatee"
        hr_director = self.env.ref("user_group.group_hr_director").users

        title = "Authority delegation Rejection"
        message = f"{self.delegatee_id.name} has rejected your request for delegation for the position of {self.delegation_position} from {self._format_date(self.delegation_start_date)} to {self._format_date(self.delegation_end_date)}."
        hr_message = f"{self.delegatee_id.name} has rejected the request for delegation for the position of {self.delegation_position} from {self._format_date(self.delegation_start_date)} to {self._format_date(self.delegation_end_date)}."
        self.send_notification(message=message, user=self.delegator_user, title=title, model=self._name, res_id=self.id)
        for user in hr_director:
            self.send_notification(message=hr_message, user=user, title=title, model=self._name, res_id=self.id)
            user.notify_warning(title=title, message=hr_message)
        self.delegator_user.notify_warning(title=title,message=message)
        self.env.user.notify_warning("Request Rejected")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Delegation',
            'res_model': self._name,
            'view_mode': 'tree,form',
            'target': 'current',
        }

    ## hr_director Approve the Authority Delegation request
    def action_approve_delegation(self):
        if not self.is_hr_director:
            raise ValidationError(_("You are not allowed to approve this request."))
        if self.status != "accepted_by_delegatee":
            raise ValidationError(_("You are not allowed to approve this request."))
        title = "Authority delegation Approval"
        message = f"Hr Director {self.env.user.employee_id.name} has approved the request for delegation for the position of {self.delegation_position} from {self._format_date(self.delegation_start_date)} to {self._format_date(self.delegation_end_date)}."
        self.send_notification(message=message, user=self.delegator_user, title=title, model=self._name, res_id=self.id)
        self.send_notification(message=message, user=self.delegatee_user, title=title, model=self._name, res_id=self.id)
        self.status = "approved"
        self.delegatee_user.notify_success(title=title,message=message)
        self.delegator_user.notify_success(title=title,message=message)
        self.env.user.notify_success("Request Approved succesfuly")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Delegation',
            'res_model': self._name,
            'view_mode': 'tree,form',
            'target': 'current',
        }

    ## hr_director reject the Authority Delegation request
    def action_reject_delegation(self):
        if not self.is_hr_director:
            raise ValidationError(_("You are not allowed to reject this request."))
        if self.status != 'accepted_by_delegatee':
            raise ValidationError(_("You are not allowed to reject this request."))
        if not self.hr_director_response:
            raise ValidationError(_("Please provide a reason for rejecting the request to the delegator."))
        title = "Authority delegation Rejection"
        message = f"Hr Director {self.env.user.employee_id.name} has rejected the request for delegation for the position of {self.delegation_position} from {self._format_date(self.delegation_start_date)} to {self._format_date(self.delegation_end_date)}."
        self.send_notification(message=message, user=self.delegator_user, title=title, model=self._name, res_id=self.id)
        self.send_notification(message=message, user=self.delegatee_user, title=title, model=self._name, res_id=self.id)
        self.status = "rejected"
        self.delegatee_user.notify_warning(title=title,message=message)
        self.delegator_user.notify_warning(title=title,message=message)
        self.env.user.notify_warning("Request Rejected.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Delegation',
            'res_model': self._name,
            'view_mode': 'tree,form',
            'target': 'current',
        }