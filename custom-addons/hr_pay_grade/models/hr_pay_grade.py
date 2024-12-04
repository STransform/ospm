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

class HrContract(models.Model):
    _inherit = "hr.contract"

    pay_grade_id = fields.Many2one(
        "hr.pay.grade",
        compute="_compute_pay_grade",
        string="Pay Grade",
        readonly=True,
        store=True,
        help="Pay grade for the contract.",
    )
    increment_level_id = fields.Many2one(
        "hr.pay.grade.increment",
        string="Increment Level",
        domain="[('pay_grade_id', '=', pay_grade_id)]",
        help="Increment level within the pay grade.",
    )
    wage = fields.Float(
        string="Wage",
        compute="_compute_wage",
        store=True,
        readonly=True,
        help="Salary based on pay grade and increment level.",
    )
    performance_score = fields.Float(
        string="Performance Score",
        help="Performance score to determine step progression.",
    )

    @api.depends("job_id")
    def _compute_pay_grade(self):
        for record in self:
            pay_grade = self.env["hr.pay.grade"].search(
                [("job_ids", "in", record.job_id.id)], limit=1
            )
            record.pay_grade_id = pay_grade

    @api.depends("pay_grade_id", "increment_level_id")
    def _compute_wage(self):
        for record in self:
            if record.increment_level_id:
                record.wage = record.increment_level_id.salary
            elif record.pay_grade_id:
                record.wage = record.pay_grade_id.base_salary
            else:
                record.wage = 0.0

    # def update_increment_based_on_performance(self):
    #     for record in self:
    #         if not record.performance_score or not record.pay_grade_id:
    #             continue

    #         increment_change = 0
    #         if 75 <= record.performance_score < 85:
    #             increment_change = 1
    #         elif 85 <= record.performance_score < 95:
    #             increment_change = 2
    #         elif record.performance_score >= 95:
    #             increment_change = 3

    #         current_increment = (
    #             int(record.increment_level_id.increment)
    #             if record.increment_level_id
    #             else 0
    #         )
    #         new_increment = current_increment + increment_change

    #         if new_increment > 9:
    #             new_increment = 9

    #         next_increment = self.env["hr.pay.grade.increment"].search(
    #             [
    #                 ("pay_grade_id", "=", record.pay_grade_id.id),
    #                 ("increment", "=", str(new_increment)),
    #             ],
    #             limit=1,
    #         )

    #         if next_increment:
    #             record.increment_level_id = next_increment
    #             record.wage = min(
    #                 next_increment.salary, record.pay_grade_id.ceiling_salary
    #             )
    #         else:
    #             record.wage = record.pay_grade_id.ceiling_salary
