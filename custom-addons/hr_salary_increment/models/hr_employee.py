from odoo import fields, models, api
from dateutil.relativedelta import relativedelta


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_eligible_for_salary_increment = fields.Boolean(
        string="Eligible for Salary Increment",
        compute="_compute_is_eligible_for_salary_increment",
        store=True,
    )

    @api.depends(
        "contract_id.increment_level_id",
        "contract_id.pay_grade_id",
    )
    def _compute_is_eligible_for_salary_increment(self):
        for employee in self:
            contract = employee.contract_id
            if not contract or not contract.pay_grade_id:
                employee.is_eligible_for_salary_increment = False
                continue

            current_step = (
                int(contract.increment_level_id.increment)
                if contract.increment_level_id
                else 0
            )

            # Eligibility conditions: not at ceiling and average score >= 75
            employee.is_eligible_for_salary_increment = (
                current_step < 9 and employee._compute_average_score() >= 75
            )

    def _compute_average_score(self):
        """Calculate the average score of the last two performance evaluations."""
        evaluations = self.env["hr.performance.evaluation"].search(
            [
                ("employee_id", "=", self.id),
                ("evaluation_status", "=", "completed"),
                (
                    "create_date",
                    ">=",
                    fields.Date.today() - relativedelta(months=12),
                ),
            ],
            order="create_date desc",
            limit=2,
        )
        total_score = sum(evaluations.mapped("total_score"))
        average_score = (
            total_score / max(len(evaluations), 1) if evaluations else 0.0
        )
        return average_score

    @api.model
    def update_employee_eligible(self):
        all_employees = self.search([])
        for employee in all_employees:
            employee._compute_is_eligible_for_salary_increment()
