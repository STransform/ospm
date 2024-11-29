from odoo import models, fields, api, _

class HrEducationProgram(models.Model):
    _name = 'hr.education.program'
    _description = 'Education Program'

    education_id = fields.Many2one('hr.education.request', string='Education Reference', required=True, ondelete='cascade', readonly=True)
    program_name = fields.Char(string='Program Name', required=True)  
    departement_id = fields.Many2one('hr.department',  string='Departement', required=True)
    employee_count = fields.Integer(string='Number of Employees', required=True)
