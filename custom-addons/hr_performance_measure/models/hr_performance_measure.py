from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrPerformanceMeasure(models.Model):
    _name = "hr.performance.measure"
    _description = "Performance Evaluation"

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="The employee being evaluated.")
    manager_id = fields.Many2one('hr.employee', string="Manager", related="employee_id.parent_id", store=True, readonly=True, help="The manager responsible for this employee.")
    period_id = fields.Many2one('hr.performance.period', string="Evaluation Period", required=True, help="The active performance evaluation period.")
    form_id = fields.Many2one('hr.performance.form', string="Evaluation Form", required=True, help="The form used for this evaluation.")
    evaluation_date = fields.Date(string="Evaluation Date", default=fields.Date.context_today, required=True)
    criteria_ids = fields.One2many('hr.performance.measure.criteria', 'performance_measure_id', string="Evaluation Criteria", help="Criteria for performance evaluation.")
    total_score = fields.Float(string="Total Score", compute="_compute_total_score", store=True, help="Total score for the evaluation.")
    overall_rating = fields.Selection([
        ('excellent', 'Excellent'),
        ('very_good', 'Very Good'),
        ('good', 'Good'),
        ('indifferent', 'Indifferent'),
        ('unsatisfactory', 'Unsatisfactory')
    ], string="Overall Rating", compute="_compute_overall_rating", store=True, help="Overall performance rating.")
    performance_score = fields.Float(string="Performance Score", compute="_compute_performance_score", store=True, help="Normalized performance score.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
    ], default='draft', string="Status", help="The status of the evaluation process.")

    @api.depends('criteria_ids.score')
    def _compute_total_score(self):
        """Compute the total score based on the evaluation criteria."""
        for record in self:
            record.total_score = sum(criteria.score for criteria in record.criteria_ids)

    @api.depends('total_score')
    def _compute_overall_rating(self):
        """Determine overall rating based on total score thresholds."""
        for record in self:
            if record.total_score >= 90:
                record.overall_rating = 'excellent'
            elif record.total_score >= 75:
                record.overall_rating = 'very_good'
            elif record.total_score >= 60:
                record.overall_rating = 'good'
            elif record.total_score >= 50:
                record.overall_rating = 'indifferent'
            else:
                record.overall_rating = 'unsatisfactory'

    @api.depends('criteria_ids')
    def _compute_performance_score(self):
        """Compute the normalized performance score."""
        for record in self:
            record.performance_score = record.total_score / len(record.criteria_ids) if record.criteria_ids else 0.0

    @api.constrains('period_id')
    def _check_period_active(self):
        """Ensure evaluations are tied to active periods."""
        for record in self:
            if not record.period_id.active:
                raise ValidationError("The selected evaluation period is not active.")

    def action_submit(self):
        """Submit the evaluation."""
        for record in self:
            if not record.criteria_ids:
                raise ValidationError("Please add at least one evaluation criterion before submitting.")
            record.state = 'submitted'

    def action_approve(self):
        """Approve the evaluation and update increment based on performance."""
        for record in self:
            if not record.employee_id.contract_id:
                raise ValidationError("The employee has no active contract.")
            record.state = 'approved'
            record.employee_id.contract_id.update_increment_based_on_performance(record.performance_score)


class HrPerformanceMeasureCriteria(models.Model):
    _name = "hr.performance.measure.criteria"
    _description = "Performance Evaluation Criteria"

    performance_measure_id = fields.Many2one('hr.performance.measure', string="Performance Measure", required=True, ondelete="cascade")
    factor_id = fields.Many2one('hr.performance.form', string="Rating Factor", required=True, help="Rating factor associated with this criterion.")
    description = fields.Text(string="Factor Description", related="factor_id.description", readonly=True)
    rating = fields.Selection([
        ('5', 'Excellent'),
        ('4', 'Very Good'),
        ('3', 'Good'),
        ('2', 'Indifferent'),
        ('1', 'Unsatisfactory'),
    ], string="Rating", required=True, help="Rating for the criterion.")
    score = fields.Float(string="Score", compute="_compute_score", store=True, help="Calculated score from rating.")

    @api.depends('rating')
    def _compute_score(self):
        """Convert the rating to a numeric score."""
        for record in self:
            record.score = int(record.rating) if record.rating else 0
