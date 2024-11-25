from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class HrPerformanceMeasure(models.Model):
    _name = "hr.performance.measure"
    _description = "Performance Evaluation"
    _order = "create_date desc"

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        domain=lambda self: self._get_subordinate_domain(),
        help="The employee being evaluated.",
    )
    evaluation_date = fields.Date(
        string="Evaluation Date",
        default=fields.Date.context_today,
        required=True,
        readonly=True,
    )
    
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        string="Status",
        help="The status of the evaluation process.",
    )
    active = fields.Boolean(string="Active", compute="_compute_active")

    @api.model
    def _get_subordinate_domain(self):
        user = self.env.user
        subordinate_ids = (
            self.env["hr.employee"].search([("parent_id.user_id", "=", user.id)]).ids
        )

        # Identify the active performance period
        active_period = self.env["hr.performance.period"].search(
            [
                ("form_activation_start_date", "<=", fields.Datetime.now()),
                ("form_activation_end_date", ">=", fields.Datetime.now()),
            ],
            limit=1,
        )

        # If no active period, return an empty domain
        if not active_period:
            return [("id", "=", -1)]

        # Get employees already evaluated for the active period
        evaluated_employee_ids = (
            self.env["hr.performance.measure"]
            .search([("period_id", "=", active_period.id)])
            .mapped("employee_id.id")
        )

        # Exclude already evaluated employees and limit to subordinates
        return [("id", "in", subordinate_ids), ("id", "not in", evaluated_employee_ids)]

    # check for employee if it is evualated
    


    def action_submit(self):
        """Submit the evaluation."""
        for record in self:
            if not record.criteria_ids:
                raise ValidationError(
                    "Please add at least one evaluation criterion before submitting."
                )
            record.state = "submitted"

    def action_approve(self):
        """Approve the evaluation and update increment based on performance."""
        for record in self:
            if not record.employee_id.contract_id:
                raise ValidationError("The employee has no active contract.")
            record.state = "approved"

    def action_reject(self):
        for record in self:
            record.state = "rejected"

