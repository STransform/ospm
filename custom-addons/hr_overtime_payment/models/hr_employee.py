from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    overtime_payment_history_ids = fields.One2many(
        'hr.overtime.payment.history', 'employee_id', string="Overtime Payment History"
    )
