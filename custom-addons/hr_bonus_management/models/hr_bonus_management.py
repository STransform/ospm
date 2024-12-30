from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrBonusmanagementBatch(models.Model):
    _name = "hr.bonus.management"
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
    is_fixed = fields.Boolean(string="Is Fixed", required=True)
    fixed_amount = fields.Float(string="Fixed Amount", tracking=True)
    months = fields.Selection(
        [("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6", "6")],
        string="How much Month",
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
    bonus_management_line = fields.One2many(
        "hr.bonus.management.line",
        "bonus_id",
        string="Bonus management Line",
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

    # add notification function
    @api.model
    def send_notification(self, message, user, title, model, res_id):
        self.env["custom.notification"].create(
            {
                "title": title,
                "message": message,
                "user_id": user.id,
                "action_model": model,
                "action_res_id": res_id,
            }
        )

    # is fixed

    def diff_month(self, date1, date2):
        return (date2.year - date1.year) * 12 + date2.month - date1.month

    # Comment Validation
    @api.depends("months")
    def _compute_name(self):
        for record in self:
            record.name = f"Bonus for {fields.Datetime.today().year} "

    @api.onchange("performance", "fixed_amount", "months", "is_fixed")
    def _onchange_bonus_management_line(self):
        self.bonus_management_line = None

    @api.onchange("is_fixed")
    def _onchange_is_fixed(self):
        self.months = None
        self.fixed_amount = None
        self.performance = None

    def action_populate_batch(self):
        """Populate batch with all employees and their bonus details."""
        employees = self.env["hr.employee"].search([("contract_id", "!=", False)])

        if not employees:
            raise ValidationError(("No employees with active contracts to process."))

        batch_lines = []
        self.bonus_management_line = None
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
                    bonus_amount = (
                        self.fixed_amount
                        if self.is_fixed
                        else contract.wage * int(self.months)
                    )

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
        self.bonus_management_line = batch_lines

    def action_submit(self):
        """Submit the batch for approval."""
        if not self.bonus_management_line:
            raise ValidationError(("The batch must contain at least one employee."))
        self.state = "submitted"
        ## search users with specific group
        hr_office = self.env.ref("user_group.group_ceo").users
        title = "Bonus Batch Submitted"
        message = f"submitted."
        for user in hr_office:
            self.send_notification(
                message=message,
                user=user,
                title=title,
                model=self._name,
                res_id=self.id,
            )
            user.notify_success(title=title, message=message)
        self.env.user.notify_success("Request Submitted")

    def action_approve(self):
        """Approve the batch and apply Bonus for eligible employees."""
        for line in self.bonus_management_line.filtered(lambda l: l.is_eligible):
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
        ## search users with specific group
        department_manager = self.env.ref("user_group.group_hr_office").users
        title = "Bonus Approved"
        message = f"approved."
        for user in department_manager:
            self.send_notification(
                message=message,
                user=user,
                title=title,
                model=self._name,
                res_id=self.id,
            )
            user.notify_success(title=title, message=message)
        self.env.user.notify_success("Bonus Approved")

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
