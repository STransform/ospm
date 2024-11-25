from odoo import models, fields, api

class PromotionApproved(models.Model):
    _name = 'promotion.approved'
    _description = 'Promotion that is approved!'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'request_name'

    request_name = fields.Text(required=True, string='Promotion Name', help='Promotion name', readonly=True)
    requested_by = fields.Text(string='Requested By', help='Requested By', readonly=True)
    state = fields.Selection(
        [
        ('pending', 'Pending'),
        ('done', 'Done'),
    ], readonly=True
    )
    number_of_recruits = fields.Integer(string='Number of Recruits', readonly=True)
    related_recruitment_id = fields.Many2one(
        'hr.recruitment.request', 
        string="Related Recruitment Request",
    ) 
    description = fields.Text(string='Description', readonly=True )
    # this is perfect enough johna
    job_position_id = fields.Many2one('hr.job', string='Job Position', required=True,   readonly=True)

    def action_change_state(self):
        for record in self:
            record.state = 'done'

    def action_post_promotion(self):
        job_title = self.request_name
        posted_by = self.env.user.name
        self.env['internal.vacancy'].create({
            'name': job_title,
            'job_description': "This Position is open for Application",
            'posted_by': posted_by,
            'job_position_id': self.job_position_id.id, 
            'number_of_recruits': self.number_of_recruits,
        })