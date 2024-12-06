from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrPayGrade(models.Model):
    _name = "hr.pay.grade"
    _description = "Pay Grade"
    
    # @api.model
    # def _select_grade(self):
    #     grades = set([i for i in range(1,17)])
    #     selected_grades = self.env['hr.pay.grade'].search([])
    #     for grade in selected_grades:
    #         grades.remove(int(grade.name))
    #     return [(str(i),f"Grade {i}") for i in sorted(grades)]

    name = fields.Selection(
        selection=[(str(i), f"Grade {i}") for i in range(1, 17)],
        string="Grade Level",
        required=True,
        help="Select the pay grade level (1-16).",
    )
    base_salary = fields.Float(string="Base Salary", required=True)
    ceiling_salary = fields.Float(string="Ceiling Salary", required=True)
    increment_steps = fields.One2many(
        "hr.pay.grade.increment", "pay_grade_id", string="Increment Steps"
    )
    job_ids = fields.Many2many(
        "hr.job",
        string="Job Positions",
        help="Job positions associated with this grade level.",
    )
    assigned_job_ids = fields.Many2many(
        "hr.job",
        compute="_compute_assigned_job_ids",
        store=False,
        string="Assigned Job Positions",
    )

    _sql_constraints = [
        ("grade_unique", "unique(name)", "Each grade must be unique."),
    ]

    def name_get(self):
        return [(record.id, f"Grade - {record.name}") for record in self]

    @api.constrains("base_salary", "ceiling_salary")
    def _check_salary_range(self):
        for record in self:
            if record.base_salary <= 0 or record.ceiling_salary <= 0:
                raise ValidationError(
                    "Base and ceiling salaries must be positive numbers."
                )
            if record.base_salary > record.ceiling_salary:
                raise ValidationError("Base salary cannot exceed ceiling salary.")

    @api.depends("job_ids")
    def _compute_assigned_job_ids(self):
        assigned_jobs = self.env["hr.pay.grade"].search([]).mapped("job_ids")
        for record in self:
            record.assigned_job_ids = assigned_jobs - record.job_ids
