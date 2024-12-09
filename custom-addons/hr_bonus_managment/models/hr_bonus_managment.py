from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrSalaryIncrementBatch(models.Model):
    _name = "hr.bonus.managment"
    _description = "HR Bonus Mnagment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Bonus Name", compute="_compute_name", required=True, tracking=True
    )
    show_filter_button = fields.Boolean(
        string="Show Filter Button",
        default=False,
    )
    months = fields.Selection(
        [("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6", "6")],
        string="How much Month",
        required=True,
        tracking=True,
    )
    performance = fields.Selection(
        [
            ("75", ">= 75"),
            ("80", ">= 80"),
            ("85", ">= 85"),
            ("90", ">= 90"),
            ("95", ">= 95"),
        ],
        string="Performance criteria",
        required=True,
        tracking=True,
    )
    bonus_managment_line = fields.One2many(
        "hr.bonus.managment.line",
        "bonus_id",
        string="Bonus Managment Line",
        readonly=True,
        tracking=True,
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
    rejection_reason = fields.Text(string="Rejection Reason", help="Reason.")

    # Comment Validation
    @api.depends("months")
    def _compute_name(self):
        for record in self:
            record.name = (
                f"Bonus for {fields.Datetime.today().year} "
                if not record.name
                else f"Bonus for {fields.Datetime.today().year} "
            )

    def action_populate_batch(self):
        """Populate batch with all employees and their bonus details."""
        employees = self.env["hr.employee"].search([("contract_id", "!=", False)])

        if not employees:
            raise ValidationError(("No employees with active contracts to process."))

        batch_lines = []
        self.bonus_managment_line = None
        for employee in employees:
            contract = employee.contract_id

            is_eligible = False
            bonus_amount = 0
            if contract:
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
                if average_score >= int(self.performance):
                    is_eligible = True
                    bonus_amount = contract.wage * int(self.months)

            # Add the employee to the batch line
            batch_lines.append(
                (
                    0,
                    0,
                    {
                        "employee_id": employee.id,
                        "current_wage": contract.wage,
                        "bonus_amount": bonus_amount,
                        "performance": average_score,
                        "is_eligible": is_eligible,
                    },
                )
            )
        self.show_filter_button = True
        self.bonus_managment_line = batch_lines

    def action_submit(self):
        """Submit the batch for approval."""
        if not self.bonus_managment_line:
            raise ValidationError(("The batch must contain at least one employee."))
        self.state = "submitted"

    def action_approve(self):
        """Approve the batch and apply Bonus for eligible employees."""
        for line in self.bonus_managment_line.filtered(lambda l: l.is_eligible):
            contract = line.employee_id.contract_id
            if not contract:
                continue

            # store  bonus history
            self.env["hr.bonus.history"].create(
                {
                    "reference": self.id,
                    "employee_id": line.employee_id.id,
                    "bonus_approved_date": fields.Datetime.now(),
                    "approved_by": self.env.user.id,
                    "bonus_amount": line.bonus_amount,
                }
            )

        self.state = "approved"

    def action_reject(self):
        """Reject the batch."""
        return {
            "name": "Reject Bonus Batch",
            "type": "ir.actions.act_window",
            "res_model": "hr.bonus.rejection.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_rejection_reason": self.rejection_reason},
        }
