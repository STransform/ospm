from odoo import api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class HrSalaryIncrement(models.Model):
    _name = "hr.salary.increment"
    _description = "HR Salary Increment"
    _rec_name = "employee_id"
    _order = "create_date desc"

    employee_id = fields.Many2one(
        "hr.employee", string="Employee", required=True, tracking=True
    )
    contract_id = fields.Many2one(
        "hr.contract",
        string="Contract",
        related="employee_id.contract_id",
        readonly=True,
        store=True,
    )
    pay_grade_id = fields.Many2one(
        "hr.pay.grade",
        string="Pay Grade",
        related="employee_id.contract_id.pay_grade_id",
    )
    current_wage = fields.Float(
        string="Current Wage",
        related="employee_id.contract_id.wage",
        readonly=True,
    )
    current_increment_level_id = fields.Many2one(
        "hr.pay.grade.increment",
        string="Current Increment Level",
        related="employee_id.contract_id.increment_level_id",
    )
    next_increment_level_id = fields.Many2one(
        "hr.pay.grade.increment",
        string="Next Increment Level",
        domain="[('pay_grade_id', '=', pay_grade_id)]",
        required=True,
        help="Select the next increment level for the employee.",
    )
    new_wage = fields.Float(
        string="New Wage",
        compute="_compute_new_wage",
        store=True,
        readonly=True,
        help="Proposed salary after the increment.",
    )
    average_score = fields.Float(
        string="Average Performance Score",
        readonly=True,
        compute="_compute_average_score",
        help="The average performance score of the last two evaluations within 6 months.",
    )
    is_valid_increment = fields.Boolean(
        string="Is Valid Increment?",
        compute="_compute_is_valid_increment",
        store=True,
        help="Indicates if the increment respects pay grade constraints.",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    remarks = fields.Text(string="Remarks", help="Approval or rejection remarks.")

    @api.depends("next_increment_level_id")
    def _compute_new_wage(self):
        """Compute the proposed new wage based on the selected increment level."""
        for record in self:
            if record.next_increment_level_id:
                record.new_wage = record.next_increment_level_id.salary
            else:
                record.new_wage = 0.0

    @api.depends("employee_id")
    def _compute_average_score(self):
        """Compute the average score of the last two performance evaluations within 6 months."""
        for record in self:
            evaluations = self.env["hr.performance.evaluation"].search(
                [
                    ("employee_id", "=", record.employee_id.id),
                    ("evaluation_status", "=", "completed"),
                    (
                        "create_date",
                        ">=",
                        fields.Date.today() - relativedelta(months=6),
                    ),
                ],
                order="create_date desc",
                limit=2,
            )
            total_score = sum(evaluations.mapped("total_score"))
            record.average_score = (
                total_score / len(evaluations) if evaluations else 0.0
            )

    @api.depends("new_wage", "employee_id.contract_id")
    def _compute_is_valid_increment(self):
        """Validate if the proposed increment respects pay grade constraints."""
        for record in self:
            if record.employee_id.contract_id.pay_grade_id:
                grade = record.employee_id.contract_id.pay_grade_id
                record.is_valid_increment = (
                    grade.base_salary <= record.new_wage <= grade.ceiling_salary
                )
            else:
                record.is_valid_increment = False

    def action_submit(self):
        """Submit the increment request for approval."""
        for record in self:
            if not record.next_increment_level_id:
                raise ValidationError("Please select the next increment level.")
            if record.average_score < 75:
                raise ValidationError(
                    "The employee's average performance score is below the required threshold."
                )
            record.state = "submitted"

    def action_approve(self):
        """Approve the increment request and update the employee's contract."""
        for record in self:
            contract = record.employee_id.contract_id
            if not contract:
                raise ValidationError("The employee does not have an active contract.")
            if not record.next_increment_level_id:
                raise ValidationError("No increment level selected for approval.")
            if not record.is_valid_increment:
                raise ValidationError(
                    "The proposed increment exceeds the allowable limits for the pay grade."
                )

            # Update contract with the selected increment level
            contract.write(
                {
                    "increment_level_id": record.next_increment_level_id.id,
                    "wage": record.next_increment_level_id.salary,
                }
            )

            record.state = "approved"
            record.remarks = (
                f"Increment approved: Updated to Increment {record.next_increment_level_id.increment} "
                f"with wage {record.next_increment_level_id.salary}."
            )

    def action_reject(self):
        """Reject the increment request."""
        for record in self:
            record.state = "rejected"
            record.remarks = "Increment request has been rejected."
