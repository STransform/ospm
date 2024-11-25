from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    promotion_ids = fields.Many2many('employee.promotion', string='Promotions',
                                     help='The promotions that an'
                                          ' employee has received')
