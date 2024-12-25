from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta

class TerminationRequest(models.Model):
    _name = 'termination.request'
    _description = 'Termination Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Request Name",
        required=True,
        readonly=True,
        default="New"
    )
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self._get_employee(), readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id', store=True)
    manager_id = fields.Many2one('hr.employee', string='Manager', related='employee_id.parent_id', store=True)
    termination_date = fields.Date(string='Termination Date', required=True)
    reason = fields.Text(string='Reason', required=True)
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'), ('requested', 'Approval Requested'), ('approved', 'Approved'), ('refused', 'Refused')],
        default='draft',
        store=True,
    )
    job_id = fields.Many2one('hr.job', string='Job Position', related='employee_id.job_id', store=True)
    state_by_service = fields.Selection(
        string='State by Manager',
        selection=[ ('resubmitted', 'Resubmitted'), ('approved', 'Approved'), ('refused', 'Refused')],
        store=True,
    )
    state_by_director = fields.Selection(
        string='State by Director',
        selection=[('resubmitted', 'Resubmitted'), ('approved', 'Approved'), ('refused', 'Refused')],
        store=True,
    )
    state_by_dceo = fields.Selection(
        string='State by DCEO',
        selection=[('resubmitted', 'Resubmitted'), ('approved', 'Approved'), ('refused', 'Refused')],
        store=True,
    )
    state_by_ceo = fields.Selection(
        string='State by CEO',
        selection=[('resubmitted', 'Resubmitted'), ('approved', 'Approved'), ('refused', 'Refused')],
        store=True,
    )
    combined_state = fields.Selection(
        string='Combined State',
        selection=[('draft', "Draft"),('processing', 'processing'),('approved', 'Approved'), ('refused', 'Refused')],
        default='draft',
        compute = '_compute_combined_state',
        store=True,
    )

    is_manager = fields.Boolean(
        string='Is Manager',
        compute='_compute_is_manager',
        store=False
    )
    is_creator = fields.Boolean(string="Is Creator", compute="_compute_is_creator", store=False)

    # termination date cannot be earlier than the current date
    @api.constrains('termination_date')
    def _check_end_date(self):
        for record in self:
            if record.termination_date and record.termination_date <= fields.Date.today():
                raise UserError("Termination Date cannot be earlier and the same than the current date.")



    @api.depends('create_uid')
    def _compute_is_creator(self):
        for record in self:
            record.is_creator = record.create_uid.id == self.env.user.id


    @api.depends('state_by_service', 'state_by_director', 'state_by_dceo', 'state_by_ceo')
    def _compute_combined_state(self):
        for record in self:
            if 'refused' in [record.state_by_service, record.state_by_director, record.state_by_dceo, record.state_by_ceo]:
                record.combined_state = 'refused'
            elif all(state == 'approved' for state in [record.state_by_service, record.state_by_director, record.state_by_dceo, record.state_by_ceo]):
                record.combined_state = 'approved'
            elif 'approved' in [record.state_by_service, record.state_by_director, record.state_by_dceo]:
                record.combined_state = 'processing'
            elif 'resubmitted' in [record.state_by_service, record.state_by_director, record.state_by_dceo, record.state_by_dceo]:
                record.combined_state = 'processing'
            else:
                record.combined_state = 'draft'



    @api.depends('manager_id')
    def _compute_is_manager(self):
        for record in self:
            record.is_manager = record.manager_id.user_id.id == self.env.uid



    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            if not employee:
                raise UserError("No employee is assigned to the current user.")
            
            new_name = f"Termination Request for {employee.name}"
            vals['name'] = new_name
        return super(TerminationRequest, self).create(vals)
    
    def _get_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

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

        # ## call this way
        # self.send_notification(message=message, user=self.delegatee_user, title=title, model=self._name, res_id=self.id)


    


    def action_by_service_request_approval(self):
        for record in self:
            record.state_by_service = 'approved'
            # send notification to the director
            director = self.env.ref("user_group.group_director").users
            title = "Termination Request"
            message = f"Termination Request for {record.employee_id.name} has been approved by the service."
            for user in director:
                self.send_notification(message = message, user = user, title = title, model = self._name, res_id = self.id) 
                user.notify_success(title=title, message=message)
            self.env.user.notify_success("Request Submitted")


    def action_by_service_refuse_request(self):
        for record in self:
            record.state_by_service = 'refused'

            title = "Termination Refused"
            message = f"Your Termination Request has been rejected."
            user = self.create_uid
            self.send_notification(message=message, user=user, title=title, model=self._name, res_id=self.id)
            self.env.user.notify_success(title=title, message=message)


    def action_by_director_request_approval(self):
        for record in self:
            record.state_by_director = 'approved'
            # send notification to the dceo
            dceo = self.env.ref("user_group.group_admin_dceo").users
            title = "Termination Request"
            message = f"Termination Request for {record.employee_id.name} has been approved by the director."
            for user in dceo:
                self.send_notification(message, user, title, model = self._name, res_id = self.id) 
                user.notify_success(title=title, message=message)
            self.env.user.notify_success("Request Submitted")

    
    def action_by_director_refuse_request(self):
        for record in self:
            record.state_by_director = 'refused'

            
            title = "Termination Refused"
            message = f"Your Termination Request has been rejected."
            user = self.create_uid
            self.send_notification(message=message, user=user, title=title, model=self._name, res_id=self.id)
            self.env.user.notify_success(title=title, message=message)

    
    def action_by_dceo_request_approval(self):
        for record in self:
            record.state_by_dceo = 'approved'
            # send notification to the ceo
            ceo = self.env.ref("user_group.group_ceo").users
            title = "Termination Request"
            message = f"Termination Request for {record.employee_id.name} has been approved by the dceo."
            for user in ceo:
                self.send_notification(message, user, title, model = self._name, res_id = self.id) 
                user.notify_success(title=title, message=message)
            self.env.user.notify_success("Request Submitted")


    def action_by_dceo_refuse_request(self):
        for record in self:
            record.state_by_dceo = 'refused'

            title = "Termination Refused"
            message = f"Your Termination Request has been rejected."
            user = self.create_uid
            self.send_notification(message=message, user=user, title=title, model=self._name, res_id=self.id)
            self.env.user.notify_success(title=title, message=message)
    
    def action_by_ceo_request_approval(self):
        for record in self:
            record.state_by_ceo = 'approved'
            # send notification to the employee
            title = "Termination Request"
            message = f"Your Termination has been approved by the ceo."
            record.employee_id.user_id.notify_success(title=title, message=message)
            self.send_notification(message, record.employee_id.user_id, title, model = self._name, res_id = self.id)
            self.env.user.notify_success("Request Approved!")

            if record.employee_id:
                # Set the employee to archived (depending on your model's definition for archived state)
                if record.employee_id.user_id:
                    record.employee_id.user_id.sudo().write({'active': False})
                record.employee_id.sudo().write({'active': False})
    
    def action_by_ceo_refuse_request(self):
        for record in self:
            record.state_by_ceo = 'refused'

            
            title = "Termination Refused"
            message = f"Your Termination Request has been rejected."
            user = self.create_uid
            self.send_notification(message=message, user=user, title=title, model=self._name, res_id=self.id)
            self.env.user.notify_success(title=title, message=message)


    def action_request_termination(self):
        for record in self:
            record.state_by_service = 'resubmitted'
            record.state_by_director = 'resubmitted'
            record.state_by_dceo = 'resubmitted'
            record.state_by_ceo = 'resubmitted'
            record.combined_state = 'processing'

            # for notification
            service_manager = record.manager_id.user_id
            title = "Termination Request"
            message = f"{record.employee_id.name} Requested Termination"
            self.send_notification(message, service_manager, title, model = self._name, res_id = self.id)

