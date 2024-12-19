from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    bonus_history_ids = fields.One2many(
        'hr.bonus.history', 'employee_id', string="Bonus History"
    )
