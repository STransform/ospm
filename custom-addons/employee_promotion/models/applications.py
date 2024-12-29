from odoo import models, fields, api

class Appilications(models.Model):
    _name = "internal.appilication"
    _description = "Model for Internal Appilications"
    _rec_name = "position"
    _order = "total desc"

    position = fields.Char(string="Position", required=True, readonly=True)
    name_of_employees = fields.Many2one('hr.employee', string="Name of Applicant",  required=True, readonly=True)
    #name_of_employee = fields.Char(string="Name of Applicant",  required=True, readonly=True)
    assesment = fields.Integer(string="Assesment", help="Assesment of the applicant")
    experience = fields.Integer(string="Experience", help="Experience of the applicant")
    interview = fields.Integer(string="Interview", help="Interview of the applicant")
    other = fields.Integer(string="Other", help="Other of the applicant")
    total = fields.Integer(string="Total Mark", compute="_compute_total", store=True, readonly=True)
    shortListed = fields.Boolean(string="Shortlisted", default=False)
    job_position_id = fields.Many2one('hr.job', string='Job Position', required=True, readonly=True)
    grouped_position = fields.Char(compute="_compute_grouped_position", store=False)
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this training session.",
    )
    vacancy_id = fields.Char(string="Vacancy ID", required=True, readonly=True)


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


    state = fields.Selection(
        [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ], readonly=True, default='pending'
    )

    @api.depends('assesment', 'experience', 'interview')
    def _compute_total(self):
        for record in self:
            record.total = record.assesment + record.experience + record.interview + record.other
            # record.total = sum([record.assesment, record.experience, record.interview])


    def action_shortlist(self):
        for record in self:
            record.shortListed = True

    def _compute_grouped_position(self):
        for record in self:
            record.grouped_position = record.position

    
    def action_refuse(self):
        for record in self:
            record.state = 'refused'

    def action_approve(self):
        for record in self:
            record.state = 'approved'
        # send notification to the employee
        self.send_notification(
            message=f"Your application for {record.position} has been approved!",
            user=record.name_of_employees.user_id,
            title="Application Approved",
            model="internal.vacancy",
            res_id=record.id
        )
        
        self.env['ceo.approved'].create({
            'position': self.position,
            'employee_id': self.name_of_employees.id,
            'job_position_id': self.job_position_id.id,
            'total_marks': self.total
        })



        