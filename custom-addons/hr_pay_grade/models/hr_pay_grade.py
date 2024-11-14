from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrPayGrade(models.Model):
    _name = "hr.pay.grade"
    _description = "Pay Grade"

    job_position_id = fields.Many2one("hr.job", string="Job Position", required=True, help="Associated job position.")
    pay_grade = fields.Integer(string="Pay Grade", required=True, help="Vertical grade level, e.g., 1, 2, 3.")
    base_salary = fields.Float(string="Base Salary", required=True, help="Base salary for this pay grade.")
    ceiling_salary = fields.Float(string="Ceiling Salary", required=True, help="Maximum salary for this pay grade.")
    increment_steps = fields.One2many("hr.pay.grade.increment", "pay_grade_id", string="Increment Steps")

    _sql_constraints = [
        ("job_position_grade_unique", "unique(job_position_id, pay_grade)", "Each job position and grade combination must be unique."),
    ]

    @api.constrains('base_salary', 'ceiling_salary')
    def _check_salary_range(self):
        for record in self:
            if record.base_salary <= 0 or record.ceiling_salary <= 0:
                raise ValidationError("Base Salary and Ceiling Salary must be positive numbers.")
            if record.base_salary > record.ceiling_salary:
                raise ValidationError("Base Salary cannot be higher than Ceiling Salary.")

    def name_get(self):
        return [(record.id, f"{record.job_position_id.name} - Grade {record.pay_grade}") for record in self]


class HrPayGradeIncrement(models.Model):
    _name = "hr.pay.grade.increment"
    _description = "Pay Grade Increment"

    pay_grade_id = fields.Many2one("hr.pay.grade", string="Pay Grade", required=True, ondelete="cascade")
    increment = fields.Integer(string="Increment Level", required=True, default=lambda self: self._default_increment_level(), help="Horizontal step within the grade, e.g., 1-9.")
    salary = fields.Float(string="Salary", required=True, help="Salary for this increment level.")

    _sql_constraints = [
        ("increment_level_unique", "unique(pay_grade_id, increment)", "Each increment level within a pay grade must be unique.")
    ]

    @api.model
    def _default_increment_level(self):
        """Auto-increment the increment level by finding the maximum existing level in the pay grade and adding 1."""
        if self._context.get('default_pay_grade_id'):
            max_increment = self.search([
                ('pay_grade_id', '=', self._context['default_pay_grade_id'])
            ], order="increment desc", limit=1)
            return max_increment.increment + 1 if max_increment else 1
        return 1

    @api.constrains('salary')
    def _check_salary_within_bounds(self):
        for record in self:
            if record.salary <= 0:
                raise ValidationError("Salary must be a positive number.")
            if not (record.pay_grade_id.base_salary <= record.salary <= record.pay_grade_id.ceiling_salary):
                raise ValidationError("Salary must be within the base and ceiling salary range of the pay grade.")


class HrContract(models.Model):
    _inherit = "hr.contract"

    pay_grade_id = fields.Many2one("hr.pay.grade", string="Pay Grade", domain="[('job_position_id', '=', job_id)]", help="Pay grade for the contract.")
    wage = fields.Float(string="Wage", compute="_compute_wage", store=True, readonly=True, help="Salary based on pay grade and increment level.")
    increment_level_id = fields.Many2one("hr.pay.grade.increment", string="Increment Level", domain="[('pay_grade_id', '=', pay_grade_id)]", help="Increment level within the pay grade.")
    performance_score = fields.Float(string="Performance Score", help="Performance score to determine step progression.")

    @api.depends('pay_grade_id', 'increment_level_id')
    def _compute_wage(self):
        for record in self:
            record.wage = record.increment_level_id.salary if record.increment_level_id else record.pay_grade_id.base_salary if record.pay_grade_id else 0.0

    def update_increment_based_on_performance(self):
        for record in self:
            if record.performance_score:
                increment_change = 0
                if 75 <= record.performance_score < 85:
                    increment_change = 1
                elif 85 <= record.performance_score < 95:
                    increment_change = 2
                elif record.performance_score >= 95:
                    increment_change = 3

                # Calculate new increment level
                current_increment = record.increment_level_id.increment if record.increment_level_id else 1
                new_increment = current_increment + increment_change

                # Find the next increment level within the same pay grade
                next_increment = record.env['hr.pay.grade.increment'].search([
                    ('pay_grade_id', '=', record.pay_grade_id.id),
                    ('increment', '=', new_increment)
                ], limit=1)

                # Update increment level if a matching increment level was found
                if next_increment:
                    record.increment_level_id = next_increment
                else:
                    # If no increment level matches, retain the current increment level
                    record.increment_level_id = record.increment_level_id
