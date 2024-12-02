from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class TrainingProgram(models.Model):
    _name = 'training.program'
    _description = 'Training Program'

    training_id = fields.Many2one('dept.request', string='Training Reference', required=True, ondelete='cascade', readonly=True)
    program_name = fields.Char(string='Program Name', required=True)  
    employee_count = fields.Integer(string='Number of Employees', required=True, default=1)  
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.onchange('employee_count')
    def _check_employee_count(self):
        for record in self:
            if record.employee_count <= 0:
                raise ValidationError("Employee count should be greater than 0.")
            
    @api.onchange('end_date')
    def _check_end_date(self):
        for record in self:
            if record.end_date and record.end_date <= record.start_date:
                raise ValidationError("End Date cannot be earlier than or the same as Start Date.")