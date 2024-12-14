from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    transfer_history_ids = fields.One2many('transfer.history', 'employee_id', string="Transfer History")
