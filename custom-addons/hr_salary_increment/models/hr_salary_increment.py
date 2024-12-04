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
    suggested_increment_level_id = fields.Many2one(
        "hr.pay.grade.increment",
        string="Suggested Increment Level",
        domain="[('pay_grade_id', '=', pay_grade_id)]",
        readonly=True,
        help="System-suggested increment level based on performance evaluation.",
    )
    next_increment_level_id = fields.Many2one(
        "hr.pay.grade.increment",
        string="Next Increment Level",
        domain="[('pay_grade_id', '=', pay_grade_id)]",
        required=True,
        help="Final increment level selected by HR.",
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
            record.new_wage = (
                record.next_increment_level_id.salary if record.next_increment_level_id else 0.0
            )

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
                total_score / max(len(evaluations), 1) if evaluations else 0.0
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

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        """Populate the suggested increment level when the employee is selected."""
        for record in self:
            if not record.employee_id:
                record.suggested_increment_level_id = False
                record.next_increment_level_id = False
                return

            # Compute the average score
            record._compute_average_score()

            # Determine the current step or check for base salary
            if not record.current_increment_level_id:
                print("Employee is on base salary.")
                current_step = 0  # Indicates base salary
            else:
                current_step = int(record.current_increment_level_id.increment)
            print("Current Step =================>", current_step)

            # Determine the step change based on performance score
            step_change = 0
            if 75 <= record.average_score < 85:
                step_change = 1
            elif 85 <= record.average_score < 95:
                step_change = 2
            elif record.average_score >= 95:
                step_change = 3

            # Calculate the suggested step and handle ceiling logic
            suggested_step = current_step + step_change
            print("Suggested Step Before Ceiling Check =================>", suggested_step)

            if suggested_step > 9:  # Cap at maximum step
                print("Suggested Step exceeds maximum increment level. Setting to ceiling salary.")
                record.suggested_increment_level_id = False
                record.next_increment_level_id = False
                record.new_wage = record.pay_grade_id.ceiling_salary  # Set to ceiling
                return

            # Convert suggested step to string for comparison
            suggested_step_str = str(suggested_step)

            # Debugging the pay_grade_id
            print("Pay Grade ID =================>", record.pay_grade_id.id)

            # Find the corresponding increment level
            suggested_increment = self.env["hr.pay.grade.increment"].search(
                [
                    ("pay_grade_id", "=", record.pay_grade_id.id),
                    ("increment", "=", suggested_step_str),
                ],
                limit=1,
            )
            print("Suggested Increment =================>", suggested_increment)

            if suggested_increment:
                record.suggested_increment_level_id = suggested_increment
                record.next_increment_level_id = suggested_increment  # Pre-fill the next increment level
                record.new_wage = suggested_increment.salary
            else:
                # Handle case where no increment matches and set to ceiling salary
                print(
                    f"No matching increment level found for Step {suggested_step_str} in Pay Grade ID {record.pay_grade_id.id}."
                )
                record.suggested_increment_level_id = False
                record.next_increment_level_id = False
                record.new_wage = record.pay_grade_id.ceiling_salary  # Set to ceiling


    def action_submit(self):
        """Submit the increment request for approval."""
        for record in self:
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
                    "wage": record.new_wage,
                }
            )

            record.state = "approved"
            record.remarks = (
                f"Increment approved: Updated to Increment {record.next_increment_level_id.increment} "
                f"with wage {record.new_wage}."
            )

    def action_reject(self):
        """Reject the increment request."""
        for record in self:
            record.state = "rejected"
            record.remarks = "Increment request has been rejected."
            record.message_post(
                body=f"Increment request for {record.employee_id.name} was rejected."
            )
