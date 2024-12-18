from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class HrSalaryIncrementBatchLine(models.Model):
    _name = "hr.salary.increment.batch.line"
    _description = "HR Salary Increment Batch Line"
    _order = "is_eligible desc"

    batch_id = fields.Many2one(
        "hr.salary.increment.batch", string="Batch", ondelete="cascade"
    )
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    steps = fields.Integer(string="Incremented By", readonly=True)
    ceiling_reached = fields.Boolean(string="Ceiling Reached", readonly=True)
    current_is_base = fields.Boolean(string="Current is Base Salary", readonly=True)
    average_performance_score = fields.Float(
        string="Average Performance Score", readonly=True
    )
    current_increment_level_id = fields.Char(
        string="Current Increment Level",
        readonly=True,
    )
    current_wage = fields.Float(string="Current Wage", readonly=True)
    new_wage = fields.Float(string="New Wage", readonly=True)
    next_increment_is_ceiling = fields.Boolean(string="Next is Ceiling", readonly=True)
    next_increment_level_id = fields.Many2one(
        "hr.pay.grade.increment",
        string="Next Increment Level",
        domain="[('pay_grade_id', '=', employee_id.contract_id.pay_grade_id)]",
        readonly=True,
    )
    is_eligible = fields.Boolean(string="Eligible for Increment", readonly=True)
    eligible_value = fields.Integer(
        string="Eligible Value", compute="_compute_eligible_value", store=True
    )
    
    @api.depends("is_eligible")
    def _compute_eligible_value(self):
        for record in self:
            record.eligible_value = 1 if record.is_eligible else 0

