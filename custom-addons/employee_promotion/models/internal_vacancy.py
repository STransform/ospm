import uuid
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta


class InternalVacancy(models.Model):
    _name = 'internal.vacancy'
    _description = 'Model for Internal Vacancy Posting'


    name = fields.Char(string='Job Title', required=True, readonly=True)
    job_description = fields.Text(string='Description', required=True, readonly=True)
    job_position_id = fields.Many2one('hr.job', string='Job Position', required=True, readonly=True)
    posted_by = fields.Text( string='Posted By', readonly=True)
    number_of_recruits = fields.Integer(string='Number of Recruits', required=True, readonly=True)
    start_date = fields.Date(string="Start Date", required=True,  default=fields.Date.today, readonly=True)
    end_date = fields.Date(string="End Date", required=True)
    remaining_days = fields.Char(string="Remaining Days", compute='_compute_remaining_days', readonly=True, store=True)
    vacancy_id = fields.Char(string="Vacancy ID", required=True, readonly=True, default=lambda self: uuid.uuid4().hex)


    def write(self, vals):
         # Ensure end_date is not modified after creation
        if 'end_date' in vals and any(record.id for record in self):
            raise ValidationError("You cannot modify the End Date after the vacancy is created.")
        return super(InternalVacancy, self).write(vals)

    @api.model
    def create(self, vals):
        # Initialize readonly behavior or additional logic here if needed
        record = super(InternalVacancy, self).create(vals)
        return record

    @api.depends('start_date', 'end_date')
    def _compute_remaining_days(self):
        for record in self:
            if record.end_date and record.start_date:
                delta = (record.end_date - date.today()).days
                if delta > 0:
                    record.remaining_days = f"{delta} days remaining"
                else:
                    record.remaining_days = "Out of Date"
            else:
                record.remaining_days = "Invalid Dates"

    def update_remaining_days(self):
        all_records = self.search([])
        all_records._compute_remaining_days()
    

    @api.constrains('end_date')
    def _check_end_date(self):
        for record in self:
            if record.end_date and record.end_date <= record.start_date:
                raise ValidationError("End Date cannot be earlier than or the same as Start Date.")

    def action_apply(self):
        # Get the employee record of the current user
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if not employee:
            raise UserError("No employee record found for the current user.")
        
        existing_application = self.env['internal.appilication'].search([
            ('name_of_employees', '=', employee.id),
            ('job_position_id', '=', self.job_position_id.id), 
            ('position', '=', self.name),
            ('vacancy_id', '=', self.vacancy_id)
        ], limit=1)

        if existing_application:
            raise ValidationError("You have already applied for this position.")


        # Create an internal application record
        self.env['internal.appilication'].create({
            'position': self.name,
            'name_of_employees': employee.id,  # Use the employee record ID
            'job_position_id': self.job_position_id.id, 
            'vacancy_id': self.vacancy_id
        })







    


    
    


