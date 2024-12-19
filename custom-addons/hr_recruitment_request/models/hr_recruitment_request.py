from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo import http
from odoo.http import request
class RecruitmentRequest(models.Model):
    _name = 'hr.recruitments'
    _description= 'recruitment module main class'
    _order = 'create_date desc'


    name = fields.Char(string='Request name', required=True)
    number_of_recruits = fields.Integer(string='Number of Recruits', required=True)
    job_position_id = fields.Many2one('hr.job', string='Job Position', required=True)
    # job_description needed on the website portal
    job_description = fields.Text(string='Job Description', store=True,readonly=False)
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    department_id = fields.Many2one('hr.department', string='Department', compute='_compute_department', store=True)
    employment_type_id = fields.Many2one('hr.contract.type', string='Employment/Contract Type')
    recruitment_type = fields.Selection([
        ('promotion', 'Promotion'),
        ('transfer', 'transfer'),
        ('external', 'External'),

    ], string='Recruitment Type')

    comment_by_hr_director = fields.Text(string='Comment by HR Director')
    comment_by_dceo = fields.Text(string='Comment by DCEO')
    comment_by_ceo = fields.Text(string='Comment by CEO')
    documents = fields.Many2many(  'ir.attachment', string='Attachments',
        help="Attach documents related to this request session"
    )
    # states by three party
    state_by_hr_director = fields.Selection([
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ])

    state_by_dceo = fields.Selection([
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ])

    state_by_ceo = fields.Selection([
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ])
    combined_state = fields.Selection([
        ('approved', 'Approved'),
        ('refused', 'Rejected'),
        ('pending', 'Pending'),
    ], string="Combined State", compute='_compute_combined_state')

    promotion_created = fields.Boolean(default=False, readonly=True)

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

    # override create method
    @api.model
    def create(self, vals):
        record = super(RecruitmentRequest, self).create(vals)
        # Send notification to HR Director
        hr_director = self.env.ref("user_group.group_hr_director").users
        title = "Recruitment Requested"
        message = f"A new recruitment request '{record.name}' has been created."
        for user in hr_director:
            self.send_notification(message, user, title, model=self._name, res_id=record.id)
            user.notify_success(title=title, message=message)
        return record


    
    

    @api.depends('state_by_hr_director', 'state_by_dceo', 'state_by_ceo')
    def _compute_combined_state(self):
        for record in self:
            # If any state is 'refused', set status to 'Rejected'
            if 'refused' in [record.state_by_hr_director, record.state_by_dceo, record.state_by_ceo]:
                record.combined_state = 'refused'
            # If all states are 'approved', set status to 'Approved'
            elif all(state == 'approved' for state in [record.state_by_hr_director, record.state_by_dceo, record.state_by_ceo]):
                record.combined_state = 'approved'
                # Call integration method when approved
                record._create_or_update_job_position()

                if record.recruitment_type == 'promotion':
                    record._create_promotion()
            # If none of them are 'approved' or 'refused', set status to 'Pending'
            else:
                record.combined_state = 'pending'

    @api.depends('created_by')
    def _compute_department(self):
        for record in self:
            employee = self.env['hr.employee'].search([('user_id', '=', record.created_by.id)], limit=1)
            record.department_id = employee.department_id if employee else False


    def action_approve_hr_director(self):
        for record in self:
            record.state_by_hr_director = 'approved'
            # send notification to the ceo
            dceo = self.env.ref("user_group.group_admin_dceo").users
            title = "Recruitment Request Approved"
            message = f"Recruitment Request has been approved by the HR Director."
            for user in dceo:
                self.send_notification(message, user, title, model = self._name, res_id = self.id) 
                user.notify_success(title=title, message=message)
            self.env.user.notify_success("Request Submitted")

    def action_reject_hr_director(self):
        for record in self:
            record.state_by_hr_director = 'refused'


    def action_approve_dceo(self):
        for record in self:
            record.state_by_dceo = 'approved'

            # send notification to the ceo
            ceo = self.env.ref("user_group.group_ceo").users
            title = "Recruitment Request Approved"
            message = f"Recruitment Request has been approved by the dceo."
            for user in ceo:
                self.send_notification(message, user, title, model = self._name, res_id = self.id) 
                user.notify_success(title=title, message=message)
            self.env.user.notify_success("Request Submitted")

        

    def action_reject_dceo(self):
        for record in self:
            record.state_by_dceo = 'refused'
    

    def action_approve_ceo(self):
        for record in self:
            record.state_by_ceo = 'approved'
            # send notification to the one created it
            title = "Recruitment Request Approved"
            message = f"Recruitment Request has been approved by the CEO."
            self.send_notification(message, record.created_by, title, model = self._name, res_id = record.id)
            record.created_by.notify_success(title=title, message=message)
    
    def action_reject_ceo(self):
        for record in self:
            record.state_by_ceo = 'refused'
    #for integrating custom recruitment request with job position
    def _create_or_update_job_position(self):
            """Create or update an hr.job record when the recruitment request is approved."""
            job_position = self.env['hr.job'].search([('id', '=', self.job_position_id.id)], limit=1)

            if job_position:
                # Update existing job position if necessary
                job_position.write({
                    'expected_employees': job_position.expected_employees + self.number_of_recruits,
                    'no_of_recruitment': self.number_of_recruits,
                    'department_id': self.department_id.id,
                    'description': self.job_description,# Ensure the job description is updated
                })
            else:
                # Create a new job position if it doesn't exist
                self.env['hr.job'].create({
                    'name': self.name,
                    'expected_employees': self.number_of_recruits,
                    'no_of_recruitment': self.number_of_recruits,
                    'department_id': self.department_id.id,
                    'employment_type_id': self.employment_type_id.id,
                    'description': self.job_description,  # Populate the description
                })
                # for the job position,

    # Method to update job description 
    def update_job_description(self):
        """This method updates the job description in the recruitment request."""
        if self.job_position_id:
            self.job_description = self.job_position_id.description

    #  Method added for creating promotion automatically
    def _create_promotion(self):
        """Automatically create a promotion in the promotion.approved model."""
        requested_by = self.created_by.name
        number_of_recruits = self.number_of_recruits
        if not self.promotion_created:
            self.env['promotion.approved'].create({
                'request_name': self.name,  # Customize this as needed
                'related_recruitment_id': self.id,  # Optional: Add a link to the recruitment request
                'requested_by': requested_by,
                'state': 'pending',
                'job_position_id': self.job_position_id.id,
                'number_of_recruits': number_of_recruits,
                'description': "Auto-registered promotion upon CEO approval.",
            })
            self.promotion_created = True