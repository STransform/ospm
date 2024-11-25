from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    transfer_ids = fields.Many2many('transfer.request', string='Transfer',
                                     help='The Transfer that an'
                                          ' employee has received')