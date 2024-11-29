from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
class EducationProgram(models.Model):
    _name = 'education.program'
    _description = 'Education Program'

    education_id = fields.Many2one('education.department.request', string='Education Reference', required=True, ondelete='cascade', readonly=True)
    program_name = fields.Char(string='Program Name', required=True)  
    employee_count = fields.Integer(string='Number of Employees', required=True, default=1)  
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.onchange("employee_count")
    def _onchange_employee_count(self):
        if self.employee_count <= 0:
            raise ValidationError("Employee count should be greter than 1.")
    