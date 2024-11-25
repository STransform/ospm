from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class InternalVacancy(models.Model):
    _name = 'internal.vacancy'
    _description = 'Model for Internal Vacancy Posting'


    name = fields.Char(string='Job Title', required=True, readonly=True)
    job_description = fields.Text(string='Description', required=True, readonly=True)
    job_position_id = fields.Many2one('hr.job', string='Job Position', required=True, readonly=True)
    posted_by = fields.Text( string='Posted By', readonly=True)
    number_of_recruits = fields.Integer(string='Number of Recruits', required=True, readonly=True)



    # def action_apply(self):
    #     position = self.name
    #     # Retrieve the currently logged-in user
    #     user = self.env.user

    #     # Fetch the employee record associated with the user
    #     employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    #     if not employee:
    #         raise ValueError("No employee record found for the current user.")

    #     # Create the internal application
    #     self.env['internal.application'].create({
    #         'position': position,
    #         'name_of_employees': employee.id,  # Save the employee ID
    #         'job_position_id': self.job_position_id.id
    #     })

    # Check if the employee has already applied for this position

    def action_apply(self):
        # Get the employee record of the current user
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if not employee:
            raise UserError("No employee record found for the current user.")
        
        existing_application = self.env['internal.appilication'].search([
            ('name_of_employees', '=', employee.id),
            ('job_position_id', '=', self.job_position_id.id), 
            ('position', '=', self.name),
        ], limit=1)

        if existing_application:
            raise ValidationError("You have already applied for this position.")


        # Create an internal application record
        self.env['internal.appilication'].create({
            'position': self.name,
            'name_of_employees': employee.id,  # Use the employee record ID
            'job_position_id': self.job_position_id.id
        })





    


    
    


