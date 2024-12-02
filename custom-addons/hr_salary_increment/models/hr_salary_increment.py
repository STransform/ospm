from odoo import api, models, fields
from odoo.exceptions import ValidationError, AccessError


class HrSalaryIncrement(models.Model):
    _name = "hr.salary.increment"
    _description = "Hr Salary Increment"
    
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, tracking=True)
