from odoo import api, models, fields
from odoo.exceptions import ValidationError, AccessError


class HrSalaryIncrement(models.Model):
    _name = "hr.salary.increment"
    _description = "Hr Salary Increment"
    _rec_name = "employee_id"
    _order = "create_date desc"

    employee_id = fields.Many2one(
        "hr.employee", string="Employee", required=True, tracking=True
    )
    contract_id = fields.Many2one(
        "hr.contract",
        string="Contract",
        related="employee_id.contract_id",
        tracking=True,
    )
    wage_id = fields.Float(
        string="Wage per Month",
        related="employee_id.contract_id.wage",
        readonly=True,
    )
    currency_id = fields.Many2one("res.currency", related="contract_id.currency_id")
    grade_id = fields.Many2one(
        "hr.pay.grade",
        string="Pay Grade",
        related="employee_id.contract_id.pay_grade_id",
        readonly=True,
    )
    increment_id = fields.Many2one(
        "hr.pay.grade.increment",
        string="Increment",
        related="employee_id.contract_id.increment_level_id",
    )
