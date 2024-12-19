from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
class HrTrainingRequest(models.Model):
    _name = 'hrtraining.request'
    _description = 'HR Training Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Request Name", 
        required=True, 
        readonly=True, 
        default="New"
    )

    training_programs = fields.One2many('hrtraining.program', 'training_id', string='Training Programs')
    description = fields.Text(string='Description')
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this training session.",
    )

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

    @api.model
    def create(self, vals):
        # Check if the name is being set dynamically
        if vals.get('name', 'New') == 'New':

            current_year = datetime.now().year
            new_name = f"Annual Training Plan - {current_year}"

            # Validate uniqueness of the name
            existing_record = self.search([('name', '=', new_name)], limit=1)
            if existing_record:
                raise ValidationError(f"Annual Training Plan for {current_year} already exists.")
            # Assign the unique name to the record
            vals['name'] = new_name

        return super(HrTrainingRequest, self).create(vals)


    state_by_ceo = fields.Selection([
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('requested', 'Approval Requested'),
        ('draft', 'Draft'),
    ], default="draft")

    state_by_planning = fields.Selection([
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('requested', 'Approval Requested'),
        ('draft', 'Draft'),
    ], default="draft")

    combined_state = fields.Selection([
        ('approved', 'Approved'),
        ('refused', 'Rejected'),
        ('requested', 'Approval Requested'),
        ('draft', 'Draft'),
    ], default="draft", string="Combined State", compute='_compute_combined_state', store=True)



    @api.depends('state_by_ceo', 'state_by_planning')
    def _compute_combined_state(self):
        for record in self:
            if 'refused' in [record.state_by_planning, record.state_by_ceo]:
                record.combined_state = 'refused'
            elif all(state == 'draft' for state in [record.state_by_planning, record.state_by_ceo]):
                record.combined_state = 'draft'
            elif all(state == 'approved' for state in [record.state_by_planning, record.state_by_ceo]):
                record.combined_state = 'approved'
            else:
                record.combined_state = 'requested'


    def action_approve_ceo(self):
        for record in self:
            record.state_by_ceo = 'approved'

            title = "Training Plan Accepted"
            message = f"Training Plan Request is Accepted."
            user = self.create_uid
            self.send_notification(message=message, user=user, title=title, model=self._name, res_id=self.id)
            self.env.user.notify_success(title=title, message=message)


    def action_reject_ceo(self):
        for record in self:
            record.state_by_ceo = 'refused'

            title = "Training Plan Refused"
            message = f"Training Plan Request has been rejected."
            user = self.create_uid
            self.send_notification(message=message, user=user, title=title, model=self._name, res_id=self.id)
            self.env.user.notify_success(title=title, message=message)

    def action_approve_planning(self):
        for record in self:
            record.state_by_planning = 'approved'
            # Notification for CEO
            title = "Training Request Approved"
            message = f"Your training request has been approved by the planning department."
            ceo = self.env.ref('user_group.group_ceo').users
            for user in ceo:
                self.send_notification(message=message, user=ceo, title=title, model=self._name, res_id=self.id)
                user.notify_success(title=title, message=message)
            self.env.user.notify_success("Request Submitted")


    def action_reject_planning(self):
        for record in self:
            record.state_by_planning = 'refused'

            # notification for department director who crated the request
            title = "Training Plan Refused"
            message = f"Training Plan Request has been rejected."
            user = self.create_uid
            self.send_notification(message=message, user=user, title=title, model=self._name, res_id=self.id)
            self.env.user.notify_success(title=title, message=message)

    def action_request_approval(self):
        for record in self:
            record.combined_state = 'requested'
            record.state_by_planning = 'requested'
            record.state_by_ceo = 'requested'
            # notification for hr manager
            planning = self.env.ref('user_group.group_planning_directorate').users
            title = "Training Plan Request"
            message = f"Training Plan Request has been submitted."
            
            for user in planning:
                self.send_notification(message=message, user=user, title=title, model=self._name, res_id=self.id)
                user.notify_success(title=title, message=message)
            self.env.user.notify_success("Request Submitted")
