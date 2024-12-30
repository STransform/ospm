from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class HrBonusmanagementLine(models.Model):
    _name = "hr.bonus.management.line"
    _description = "HR Bonus management Line"
    _order = "is_eligible desc"

    bonus_id = fields.Many2one(
        "hr.bonus.management", string="Bonus", ondelete="cascade"
    )
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    employee_department = fields.Many2one(related='employee_id.department_id')
    current_wage = fields.Float(string="Current Wage per Month", required=True)
    bonus_amount = fields.Float(string="Bonus Amount", readonly=True)
    is_eligible = fields.Boolean(string="Eligible for Bonus", readonly=True)
    performance = fields.Float(string="Performance Score", readonly=True)