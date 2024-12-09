from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class HrBonusManagmentLine(models.Model):
    _name = "hr.bonus.managment.line"
    _description = "HR Bonus Managment Line"
    _order = "is_eligible desc"

    bonus_id = fields.Many2one(
        "hr.bonus.managment", string="Bonus", ondelete="cascade"
    )
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    current_wage = fields.Float(string="Current Wage per Month", required=True)
    bonus_amount = fields.Float(string="Bonus Amount", readonly=True)
    is_eligible = fields.Boolean(string="Eligible for Bonus", readonly=True)