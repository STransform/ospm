from odoo import models, fields, api, _

class TrainingProgramForHr(models.Model):
    _name = 'hrtraining.program'
    _description = 'Training Program'

    training_id = fields.Many2one('hrtraining.request', string='Training Reference', required=True, ondelete='cascade', readonly=True)
    program_name = fields.Char(string='Program Name', required=True)  
    departement_id = fields.Many2one('hr.department',  string='Departement', required=True)
    employee_count = fields.Integer(string='Number of Employees', required=True)
