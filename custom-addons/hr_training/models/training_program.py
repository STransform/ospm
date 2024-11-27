from odoo import models, fields, api, _

class TrainingProgram(models.Model):
    _name = 'training.program'
    _description = 'Training Program'

    training_id = fields.Many2one('dept.request', string='Training Reference', required=True, ondelete='cascade', readonly=True)
    program_name = fields.Char(string='Program Name', required=True)  
    employee_count = fields.Integer(string='Number of Employees', required=True)  
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)