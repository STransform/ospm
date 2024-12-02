from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class TrainingProgramForHr(models.Model):
    _name = 'hrtraining.program'
    _description = 'Training Program'

    training_id = fields.Many2one('hrtraining.request', string='Training Reference', required=True, ondelete='cascade', readonly=True)
    program_name = fields.Char(string='Program Name', required=True)  
    departement_id = fields.Many2one('hr.department',  string='Departement', required=True)
    employee_count = fields.Integer(string='Number of Employees', required=True, default=1)

    # employee count should not be 0 0r negative
    @api.onchange('employee_count')
    def _check_employee_count(self):
        for record in self:
            if record.employee_count <= 0:
                raise ValidationError("Employee count should be greater than 0.")