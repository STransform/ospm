from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo import http
from odoo.http import request
class RecruitmentRequest(models.Model):
    _name = 'hr.recruitments'
    _description= 'recruitment module main class'


    name = fields.Char(string='Request name', required=True)
    number_of_recruits = fields.Integer(string='Number of Recruits', required=True)
    job_position_id = fields.Many2one('hr.job', string='Job Position', required=True)
    # job_description needed on the website portal
    job_description = fields.Text(string='Job Description', compute='_compute_job_description', store=True,readonly=False)
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

    def action_reject_hr_director(self):
        for record in self:
            record.state_by_hr_director = 'refused'


    def action_approve_dceo(self):
        for record in self:
            record.state_by_dceo = 'approved'
        

    def action_reject_dceo(self):
        for record in self:
            record.state_by_dceo = 'refused'
    

    def action_approve_ceo(self):
        for record in self:
            record.state_by_ceo = 'approved'
    
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
    #to correctly display the job_description from the hr.recruitments model on the website, 
    #The _compute_job_description method links the job_description in hr.recruitments with the description field of the hr.job model when the job_position_id is set.
    #This ensures that the job_description field is updated dynamically whenever the job position changes.
    @api.depends('job_position_id')
    def _compute_job_description(self):
        for record in self:
            record.job_description = record.job_position_id.description if record.job_position_id else ''


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