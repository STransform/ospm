from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrSalaryIncrementBatch(models.Model):
    _name = "hr.salary.increment.batch"
    _description = "HR Salary Increment Batch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Batch Name", compute="_compute_name", required=True, tracking=True
    )
    show_filter_button = fields.Boolean(string="Show Filter Button", default=False)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
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
    increment_line_ids = fields.One2many(
        "hr.salary.increment.batch.line",
        "batch_id",
        string="Increment Lines",
        readonly=True,
    )
    rejection_reason = fields.Text(string="Rejection Reason", help="Reason.")

    @api.depends("start_date", "end_date")
    def _compute_name(self):
        for record in self:
            record.name = (
                f"Salary Increment from {record.start_date.day}/{record.end_date.month}/{record.start_date.year} to {record.start_date.day}//{record.end_date.month}/{record.end_date.year} ({self.diff_month(record.start_date, record.end_date)}) months"
                if record.start_date and record.end_date
                else "Salary Increment from"
            )

        # month calculation

    def diff_month(self, date1, date2):
        return (date2.year - date1.year) * 12 + date2.month - date1.month

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for record in self:
            if (
                record.end_date
                and record.start_date
                and record.end_date < record.start_date
            ):
                raise ValidationError("'End' date cannot be earlier than 'Start' date.")
            if (
                record.end_date
                and record.start_date
                and self.diff_month(record.start_date, record.end_date) < 12
            ):
                raise ValidationError(
                    "Salary increment period cannot be less than 12 month"
                )

    @api.onchange("start_date", "end_date")
    def _check_overlap(self):
        if self.start_date and self.end_date:
            salary_increments = self.env["hr.salary.increment.batch"].search([])
            for salary_increment in salary_increments:
                if (
                    salary_increment.start_date
                    <= self.start_date
                    <= salary_increment.end_date
                ) and salary_increment.state != "rejected":
                    raise ValidationError(
                        f"Salary Increment Request cannot be duplicated! exist in {salary_increment.name}"
                    )
                if (
                    salary_increment.start_date
                    <= self.end_date
                    <= salary_increment.end_date
                ) and salary_increment.state != "rejected":
                    raise ValidationError(
                        f"Salary Increment Request cannot be duplicated! exist in {salary_increment.name}"
                    )

    def action_populate_batch(self):
        """Populate batch with all employees and their increment details."""
        employees = self.env["hr.employee"].search([("contract_id", "!=", False)])

        if not employees:
            raise ValidationError(("No employees with active contracts to process."))

        batch_lines = []
        self.increment_line_ids = None
        for employee in employees:
            contract = employee.contract_id

            # Initialize default values
            steps = 0
            average_score = 0
            is_eligible = False
            suggested_increment = None
            new_wage = contract.wage if contract else 0.0
            if (
                contract
                and contract.increment_level_id
                or contract
                and contract.is_base
                or contract
                and contract.is_ceiling
            ):
                # Calculate average score
                evaluations = self.env["hr.performance.evaluation"].search(
                    [
                        ("employee_id", "=", employee.id),
                        ("evaluation_status", "=", "completed"),
                    ],
                    order="create_date desc",
                    limit=2,
                )
                total_score = sum(evaluations.mapped("total_score"))
                average_score = (
                    total_score / max(len(evaluations), 1) if evaluations else 0.0
                )

                # Check eligibility
                current_step = int(contract.increment_level_id.increment or 0)
                if average_score >= 75 and current_step < 9 and not contract.is_ceiling:
                    is_eligible = True
                    step_change = (
                        1
                        if 75 <= average_score < 85
                        else 2 if 85 <= average_score < 95 else 3
                    )
                    steps = step_change
                    suggested_step = min(current_step + step_change, 9)

                    suggested_increment = self.env["hr.pay.grade.increment"].search(
                        [
                            ("pay_grade_id", "=", contract.pay_grade_id.id),
                            ("increment", "=", str(suggested_step)),
                        ],
                        limit=1,
                    )
                    new_wage = (
                        suggested_increment.salary
                        if suggested_increment
                        else contract.wage
                    )

            # Add the employee to the batch line
            batch_lines.append(
                (
                    0,
                    0,
                    {
                        "employee_id": employee.id,
                        "current_is_base": True if contract.is_base else False,
                        "current_increment_level_id": (
                            contract.increment_level_id
                            if contract.increment_level_id
                            else False
                        ),
                        "average_performance_score": average_score,
                        "ceiling_reached": True if contract.is_ceiling else False,
                        "current_wage": contract.wage if contract else 0.0,
                        "steps": steps,
                        "new_wage": (
                            contract.pay_grade_id.ceiling_salary
                            if is_eligible and not suggested_increment
                            else new_wage
                        ),
                        "next_increment_level_id": (
                            suggested_increment.id if suggested_increment else False
                        ),
                        "next_increment_is_ceiling": (
                            True if is_eligible and not suggested_increment else False
                        ),
                        "is_eligible": is_eligible,
                    },
                )
            )
        self.show_filter_button = True
        self.increment_line_ids = batch_lines

    def action_submit(self):
        """Submit the batch for approval."""
        if not self.increment_line_ids:
            raise ValidationError(("The batch must contain at least one employee."))
        self.state = "submitted"

    def action_approve(self):
        """Approve the batch and apply increments for eligible employees."""
        for line in self.increment_line_ids.filtered(lambda l: l.is_eligible):
            contract = line.employee_id.contract_id
            if not contract:
                continue

            # store  increment history
            self.env["hr.salary.increment.history"].create(
                {
                    "employee_id": line.employee_id.id,
                    "increment_date": fields.Datetime.now(),
                    "approved_by": self.env.user.id,
                    "from_increment_name": (
                        line.current_increment_level_id.display_name
                        if line.current_increment_level_id
                        else "Base"
                    ),
                    "to_increment_name": (
                        line.next_increment_level_id.display_name
                        if not line.next_increment_is_ceiling
                        else "Ceiling"
                    ),
                }
            )
            contract.write(
                {
                    "is_base": False,
                    "is_ceiling": True if line.next_increment_is_ceiling else False,
                    "increment_level_id": (
                        line.next_increment_level_id.id
                        if not line.next_increment_is_ceiling
                        else False
                    ),
                    "wage": line.new_wage,
                }
            )

        self.state = "approved"

    def action_reject(self):
        """Reject the batch."""
        return {
            "name": "Reject Incrment Batch",
            "type": "ir.actions.act_window",
            "res_model": "hr.salary.increment.batch.rejection.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_rejection_reason": self.rejection_reason},
        }
