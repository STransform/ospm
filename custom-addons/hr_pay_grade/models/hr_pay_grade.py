from odoo import api, fields, models
from odoo.exceptions import ValidationError

class HrPayGrade(models.Model):
    _name = "hr.pay.grade"
    _description = "Pay Grade"

    job_position_id = fields.Many2one("hr.job", string="Job Position", required=True, help="Associated job position.")
    grade_name = fields.Char(string="Grade", required=True, help="Grade level, e.g., A, B, C.")
    salary = fields.Float(string="Salary", required=True, help="Fixed salary for this grade level.")

    _sql_constraints = [
        ("job_position_grade_unique", "unique(job_position_id, grade_name)", "Each job position and grade combination must be unique."),
    ]

    @api.constrains('salary')
    def _check_salary_positive(self):
        for record in self:
            if record.salary < 0:
                raise ValidationError("Salary must be a positive number.")

    def name_get(self):
        return [(record.id, f"{record.job_position_id.name} - {record.grade_name}") for record in self]


class HrContract(models.Model):
    _inherit = "hr.contract"

    pay_grade_id = fields.Many2one("hr.pay.grade", string="Pay Grade", domain="[('job_position_id', '=', job_id)]", help="Pay grade for the contract.")
    wage = fields.Float(string="Wage", compute="_compute_wage", store=True, readonly=True, help="Salary derived from the pay grade.")

    @api.depends('pay_grade_id')
    def _compute_wage(self):
        for record in self:
            record.wage = record.pay_grade_id.salary if record.pay_grade_id else 0.0
