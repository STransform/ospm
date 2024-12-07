from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    salary_increment_history_ids = fields.One2many(
        'hr.salary.increment.history', 'employee_id', string="Salary Increment History"
    )
