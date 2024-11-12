from odoo import api, fields, models
from odoo.exceptions import ValidationError

class HrPayGrade(models.Model):
    _name = "hr.pay.grade"
    _description = "Pay Grade"

    job_position_id = fields.Many2one("hr.job", string="Job Position", required=True, help="Job position associated with this grade.")
    grade_name = fields.Char(string="Grade", required=True, help="Grade level, e.g., A, B, C.")
    salary = fields.Float(string="Salary", required=True, help="Fixed salary for this grade level.")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("job_position_grade_unique", "unique(job_position_id, grade_name)", "Each job position and grade combination must be unique."),
    ]

    @api.constrains('salary')
    def _check_salary_positive(self):
        for record in self:
            if record.salary < 0:
                raise ValidationError("Salary must be a positive number.")

    @api.onchange('salary')
    def _validate_salary_onchange(self):
        if self.salary < 0:
            return {
                'warning': {
                    'title': "Invalid Input",
                    'message': "Salary must be a positive number."
                }
            }

class HrJob(models.Model):
    _inherit = "hr.job"

    pay_grade_ids = fields.One2many("hr.pay.grade", "job_position_id", string="Grades", help="Defines salary for each grade within this job position.")
    

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    job_id = fields.Many2one("hr.job", string="Job Position")
    pay_grade_id = fields.Many2one("hr.pay.grade", string="Pay Grade", domain="[('job_position_id', '=', job_id)]")
    current_salary = fields.Float(string="Current Salary", compute="_compute_current_salary", store=True)

    @api.depends('pay_grade_id')
    def _compute_current_salary(self):
        for record in self:
            record.current_salary = record.pay_grade_id.salary if record.pay_grade_id else 0.0
