from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class RecruitmentRequest(models.Model):
    _name = 'hr.recruitments'
    _description= 'Training module main class'

    name = fields.Char(string='name', required=True)
    number_of_recruits = fields.Integer(string='Number of Recruits', required=True)
    job_position_id = fields.Many2one('hr.job', string='Job Position', required=True)
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
                record._create_job_position()

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


    def _create_job_position(self):
        job_name = f"Position Approved by CEO: {self.name}"  # Customize the name as needed
        number_of_rec = self.number_of_recruits

        # Check if hr.recruitment model is accessible and create a new job
        self.env['hr.job'].create({
            'name': job_name,
            'no_of_recruitment': number_of_rec,
            'description': "Automatically created position upon CEO approval.",
            # Add other required fields as necessary, such as department_id or expected_employee
        })

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


