from odoo import models, fields, api

class CEOApproved(models.Model):
    _name = "ceo.approved"
    _description = "Model for CEO Approved Applications"
    _rec_name = "position"
    _order = "total_marks desc"

    position = fields.Char(string="Position", required=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Name of Applicant",  required=True, readonly=True)
    job_position_id = fields.Many2one('hr.job', string='Job Position', required=True, readonly=True)
    total_marks = fields.Integer(string="Total Marks", required=True, readonly=True)



    def action_start_hiring(self):
            """Open the promotion view with pre-filled data."""
            return {
                'type': 'ir.actions.act_window',
                'name': 'Start Hiring',
                'res_model': 'employee.promotion',
                'view_mode': 'form',
                'view_id': self.env.ref('employee_promotion.employee_promotion_view_form').id,  # Replace with your view ID
                'target': 'new', 
                'context': {
                    'default_promotion_name': self.position,
                    'default_employee_id': self.employee_id.id,
                    'default_job_position_id': self.job_position_id.id,
                },
            }




