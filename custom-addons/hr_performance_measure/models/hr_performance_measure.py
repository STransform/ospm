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
    period_id = fields.Many2one(
        "hr.performance.period",
        string="Evaluation Period",
        required=True,
        help="The active performance evaluation period.",
    )
    evaluation_date = fields.Date(
        string="Evaluation Date",
        default=fields.Date.context_today,
        required=True,
        readonly=True,
    )
    criteria_ids = fields.One2many(
        "hr.performance.measure.criteria",
        "performance_id",
        string="Evaluation Criteria",
        help="Criteria for performance evaluation.",
    )
    total_score = fields.Float(
        string="Total Score",
        compute="_compute_total_score",
        store=True,
        help="Total score for the evaluation.",
    )
    overall_rating = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("very_good", "Very Good"),
            ("good", "Good"),
            ("indifferent", "Indifferent"),
            ("unsatisfactory", "Unsatisfactory"),
        ],
        string="Overall Rating",
        compute="_compute_overall_rating",
        store=True,
        help="Overall performance rating.",
    )
    performance_score = fields.Float(
        string="Performance Score",
        compute="_compute_performance_score",
        store=True,
        help="Normalized performance score.",
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
    @api.depends("criteria_ids.score")
    def _compute_total_score(self):
        """Compute the total score based on the evaluation criteria."""
        for record in self:
            record.total_score = sum(criteria.score for criteria in record.criteria_ids)

    @api.depends("total_score")
    def _compute_overall_rating(self):
        """Determine overall rating based on total score thresholds."""
        for record in self:
            if record.total_score >= 90:
                record.overall_rating = "excellent"
            elif record.total_score >= 75:
                record.overall_rating = "very_good"
            elif record.total_score >= 60:
                record.overall_rating = "good"
            elif record.total_score >= 50:
                record.overall_rating = "indifferent"
            else:
                record.overall_rating = "unsatisfactory"

    @api.depends("criteria_ids")
    def _compute_performance_score(self):
        """Compute the normalized performance score."""
        for record in self:
            record.performance_score = (
                record.total_score / len(record.criteria_ids)
                if record.criteria_ids
                else 0.0
            )

    @api.constrains("period_id")
    def _check_period_active(self):
        """Ensure evaluations are tied to active periods."""
        for record in self:
            if not record.period_id.active:
                raise ValidationError("The selected evaluation period is not active.")

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

