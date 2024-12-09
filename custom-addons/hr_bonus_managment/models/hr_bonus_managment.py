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
        string="Show Filter Button", default=False, tracking=True
    )
    months = fields.Selection(
        [("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6", "6")],
        string="For How much Month",
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
    remarks = fields.Text(string="Remarks", help="Batch-level remarks.")

    @api.depends("months")
    def _compute_name(self):
        for record in self:
            record.name = (
                f"Bonus for {fields.Datetime.today().year} "
                if not record.name
                else f"Bonus for {fields.Datetime.today().year} "
            )

    # def action_populate_batch(self):
    #     """Populate batch with all employees and their increment details."""
    #     employees = self.env["hr.employee"].search([("contract_id", "!=", False)])

    #     if not employees:
    #         raise ValidationError(("No employees with active contracts to process."))

    #     batch_lines = []
    #     for employee in employees:
    #         contract = employee.contract_id

    #         # Initialize default values
    #         steps = 0
    #         average_score = 0
    #         is_eligible = False
    #         suggested_increment = None
    #         new_wage = contract.wage if contract else 0.0
    #         if (
    #             contract
    #             and contract.increment_level_id
    #             or contract
    #             and contract.is_base
    #             or contract
    #             and contract.is_ceiling
    #         ):
    #             # Calculate average score
    #             evaluations = self.env["hr.performance.evaluation"].search(
    #                 [
    #                     ("employee_id", "=", employee.id),
    #                     ("evaluation_status", "=", "completed"),
    #                 ],
    #                 order="create_date desc",
    #                 limit=2,
    #             )
    #             total_score = sum(evaluations.mapped("total_score"))
    #             average_score = (
    #                 total_score / max(len(evaluations), 1) if evaluations else 0.0
    #             )

    #             # Check eligibility
    #             current_step = int(contract.increment_level_id.increment or 0)
    #             if average_score >= 75 and current_step < 9 and not contract.is_ceiling:
    #                 is_eligible = True
    #                 step_change = (
    #                     1
    #                     if 75 <= average_score < 85
    #                     else 2 if 85 <= average_score < 95 else 3
    #                 )
    #                 steps = step_change
    #                 suggested_step = min(current_step + step_change, 9)

    #                 suggested_increment = self.env["hr.pay.grade.increment"].search(
    #                     [
    #                         ("pay_grade_id", "=", contract.pay_grade_id.id),
    #                         ("increment", "=", str(suggested_step)),
    #                     ],
    #                     limit=1,
    #                 )
    #                 new_wage = (
    #                     suggested_increment.salary
    #                     if suggested_increment
    #                     else contract.wage
    #                 )

    #         # Add the employee to the batch line
    #         batch_lines.append(
    #             (
    #                 0,
    #                 0,
    #                 {
    #                     "employee_id": employee.id,
    #                     "current_is_base": True if contract.is_base else False,
    #                     "current_increment_level_id": (
    #                         contract.increment_level_id
    #                         if contract.increment_level_id
    #                         else False
    #                     ),
    #                     "average_performance_score": average_score,
    #                     "ceiling_reached": True if contract.is_ceiling else False,
    #                     "current_wage": contract.wage if contract else 0.0,
    #                     "steps": steps,
    #                     "new_wage": (
    #                         contract.pay_grade_id.ceiling_salary
    #                         if is_eligible and not suggested_increment
    #                         else new_wage
    #                     ),
    #                     "next_increment_level_id": (
    #                         suggested_increment.id if suggested_increment else False
    #                     ),
    #                     "next_increment_is_ceiling": (
    #                         True if is_eligible and not suggested_increment else False
    #                     ),
    #                     "is_eligible": is_eligible,
    #                 },
    #             )
    #         )
    #     self.show_filter_button = True
    #     self.increment_line_ids = batch_lines

    # def action_submit(self):
    #     """Submit the batch for approval."""
    #     if not self.increment_line_ids:
    #         raise ValidationError(("The batch must contain at least one employee."))
    #     self.state = "submitted"

    # def action_approve(self):
    #     """Approve the batch and apply increments for eligible employees."""
    #     for line in self.increment_line_ids.filtered(lambda l: l.is_eligible):
    #         contract = line.employee_id.contract_id
    #         if not contract:
    #             continue

    #         # store  increment history
    #         self.env["hr.salary.increment.history"].create(
    #             {
    #                 "employee_id": line.employee_id.id,
    #                 "increment_date": fields.Datetime.now(),
    #                 "approved_by": self.env.user.id,
    #                 "from_increment_name": (
    #                     line.current_increment_level_id.display_name
    #                     if line.current_increment_level_id
    #                     else "Base"
    #                 ),
    #                 "to_increment_name": (
    #                     line.next_increment_level_id.display_name
    #                     if not line.next_increment_is_ceiling
    #                     else "Ceiling"
    #                 ),
    #             }
    #         )
    #         contract.write(
    #             {
    #                 "is_base": False,
    #                 "is_ceiling": True if line.next_increment_is_ceiling else False,
    #                 "increment_level_id": (
    #                     line.next_increment_level_id.id
    #                     if not line.next_increment_is_ceiling
    #                     else False
    #                 ),
    #                 "wage": line.new_wage,
    #             }
    #         )

    #     self.state = "approved"

    # def action_reject(self):
    #     """Reject the batch."""
    #     self.state = "rejected"
