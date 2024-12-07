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
    steps = fields.Integer(string="Incrmented By", readonly=True)
    ceiling_reached = fields.Boolean(string="Ceiling Reached", readonly=True)
    current_is_base = fields.Boolean(string="Current is Base Salary", readonly=True)
    average_performance_score = fields.Float(
        string="Average Performance Score", readonly=True
    )
    current_increment_level_id = fields.Many2one(
        "hr.pay.grade.increment",
        string="Current Increment Level",
        related="employee_id.contract_id.increment_level_id",
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


# class HrSalaryIncrementBatchLine(models.Model):
#     _name = "hr.salary.increment.batch.line"
#     _description = "HR Salary Increment Batch Line"

#     batch_id = fields.Many2one(
#         "hr.salary.increment.batch", string="Batch", ondelete="cascade"
#     )
#     employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
#     contract_id = fields.Many2one(
#         "hr.contract",
#         string="Contract",
#         related="employee_id.contract_id",
#         readonly=True,
#         store=True,
#     )
#     pay_grade_id = fields.Many2one(
#         "hr.pay.grade",
#         string="Pay Grade",
#         related="employee_id.contract_id.pay_grade_id",
#         readonly=True,
#         store=True,
#     )
#     current_wage = fields.Float(
#         string="Current Wage", related="employee_id.contract_id.wage", readonly=True
#     )
#     new_wage = fields.Float(string="New Wage", readonly=True)
#     next_increment_level_id = fields.Many2one(
#         "hr.pay.grade.increment",
#         string="Next Increment Level",
#         domain="[('pay_grade_id', '=', pay_grade_id)]",
#         required=True,
#     )

#     def all_eligiable_employee(self):
#         employees = self.env["hr.employee"].search([])
#         eligiable_employees = []
#         for employee in employees:
#             employee_result = self._compute_is_eligible(employee)
#             if employee_result[0]:
#                 suggested_step = self._compute_next_increment_level(
#                     employee_result[1], employee_result[2]
#                 )
#                 suggested_increment = self.env["hr.pay.grade.increment"].search(
#                     [
#                         ("pay_grade_id", "=", employee.contract_id.pay_grade_id.id),
#                         ("increment", "=", str(suggested_step)),
#                     ],
#                     limit=1,
#                 )
#                 employee_next_increment = {
#                     "employee_id": employee.id,
#                     "contract_id": employee.contract_id,
#                     "pay_grade_id": employee.contract_id.pay_grade_id,
#                     "current_wage": employee.contract_id.wage,
#                     "new_wage": suggested_increment.salary,
#                     "next_increment_level_id": suggested_increment.id,
#                 }

#                 eligiable_employees.append(employee_next_increment)

#         return eligiable_employees

#     def _compute_next_increment_level(average_score, current_step):
#         step_change = 0
#         if 75 <= average_score < 85:
#             step_change = 1
#         elif 85 <= average_score < 95:
#             step_change = 2
#         elif average_score >= 95:
#             step_change = 3

#         return min(current_step + step_change, 9)

#     def _compute_is_eligible(self):
#         """Determine if the employee is eligible for a salary increment."""
#         if (
#             not self.employee_id.contract_id.pay_grade_id
#             or not self.employee_id.contract_id.active
#         ):
#             return (False, 0, 0)

#         current_step = (
#             int(self.employee_id.contract_id.increment_level_id.increment)
#             if self.employee_id.contract_id.increment_level_id
#             else 0
#         )

#         # Eligibility conditions: not at ceiling and average score >= 75
#         average_score = self._compute_average_score(self)
#         return (current_step < 9 and average_score >= 75, average_score, current_step)

#     def _compute_average_score(self):
#         """Calculate the average score of the last two performance evaluations."""

#         evaluations = self.env["hr.performance.evaluation"].search(
#             [
#                 ("employee_id", "=", self.employee_id.id),
#                 ("evaluation_status", "=", "completed"),
#             ],
#             order="create_date desc",
#             limit=2,
#         )
#         total_score = sum(evaluations.mapped("total_score"))
#         return total_score / max(len(evaluations), 1) if evaluations else 0.0
