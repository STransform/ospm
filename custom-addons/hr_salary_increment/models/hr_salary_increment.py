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
        readonly=True,
        store=True,
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
        readonly=True,
    )
    suggested_increment_level_id = fields.Many2one(
        "hr.pay.grade.increment",
        string="Suggested Increment Level",
        domain="[('pay_grade_id', '=', pay_grade_id)]",
        readonly=True,
        compute="_compute_suggested_increment_level",
        store=True,
    )
    next_increment_level_id = fields.Many2one(
        "hr.pay.grade.increment",
        string="Next Increment Level",
        domain="[('pay_grade_id', '=', pay_grade_id)]",
        required=True,
    )
    new_wage = fields.Float(
        string="New Wage",
        compute="_compute_new_wage",
        store=True,
        readonly=True,
    )
    average_score = fields.Float(
        string="Average Performance Score",
        readonly=True,
        compute="_compute_average_score",
    )
    is_eligible = fields.Boolean(
        string="Eligible for Increment?",
        compute="_compute_is_eligible",
        store=True,
        help="Indicates if the employee is eligible for a salary increment.",
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
        """Calculate the average score of the last two performance evaluations."""
        for record in self:
            evaluations = self.env["hr.performance.evaluation"].search(
                [
                    ("employee_id", "=", record.employee_id.id),
                    ("evaluation_status", "=", "completed"),
                    ("create_date", ">=", fields.Date.today() - relativedelta(months=6)),
                ],
                order="create_date desc",
                limit=2,
            )
            total_score = sum(evaluations.mapped("total_score"))
            record.average_score = (
                total_score / max(len(evaluations), 1) if evaluations else 0.0
            )

    @api.depends("pay_grade_id", "average_score", "current_increment_level_id")
    def _compute_is_eligible(self):
        """Determine if the employee is eligible for a salary increment."""
        for record in self:
            if not record.pay_grade_id:
                record.is_eligible = False
                continue

            current_step = (
                int(record.current_increment_level_id.increment)
                if record.current_increment_level_id
                else 0
            )
            record.is_eligible = current_step < 9 and record.average_score >= 75

    @api.depends("current_increment_level_id", "average_score", "pay_grade_id")
    def _compute_suggested_increment_level(self):
        """Compute the suggested increment level based on performance."""
        for record in self:
            if not record.pay_grade_id or record.average_score < 75:
                record.suggested_increment_level_id = False
                continue

            current_step = (
                int(record.current_increment_level_id.increment)
                if record.current_increment_level_id
                else 0
            )
            step_change = (
                1 if 75 <= record.average_score < 85
                else 2 if 85 <= record.average_score < 95
                else 3 if record.average_score >= 95
                else 0
            )
            suggested_step = min(current_step + step_change, 9)
            record.suggested_increment_level_id = self.env[
                "hr.pay.grade.increment"
            ].search(
                [
                    ("pay_grade_id", "=", record.pay_grade_id.id),
                    ("increment", "=", str(suggested_step)),
                ],
                limit=1,
            )

    def action_submit(self):
        """Submit the salary increment request."""
        for record in self:
            if not record.is_eligible:
                raise ValidationError("The employee is not eligible for a salary increment.")
            record.state = "submitted"

    def action_approve(self):
        """Approve the salary increment request."""
        for record in self:
            contract = record.employee_id.contract_id
            if not contract:
                raise ValidationError("The employee does not have an active contract.")
            if not record.next_increment_level_id:
                raise ValidationError("No increment level selected for approval.")

            # Update the contract based on the selected increment level
            contract.write(
                {
                    "increment_level_id": record.next_increment_level_id.id,
                    "wage": record.new_wage,
                }
            )
            record.remarks = (
                f"Increment approved: Updated to Increment {record.next_increment_level_id.increment} "
                f"with wage {record.new_wage}."
            )
            record.state = "approved"

    def action_reject(self):
        """Reject the salary increment request."""
        for record in self:
            record.state = "rejected"
            record.remarks = "Increment request has been rejected."
