from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrPerformanceMeasure(models.Model):
    _name = "hr.performance.measure"
    _description = "Performance Evaluation"
    _order = 'create_date desc'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="The employee being evaluated.")
    period_id = fields.Many2one('hr.performance.period', string="Evaluation Period", required=True, help="The active performance evaluation period.")
    evaluation_date = fields.Date(string="Evaluation Date", default=fields.Date.context_today, required=True, readonly=True)
    criteria_ids = fields.One2many('hr.performance.measure.criteria', 'performance_id', string="Evaluation Criteria", help="Criteria for performance evaluation.")
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
        ('rejected', 'Rejected')
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

    @api.onchange('period_id')
    def _onchange_period_id(self):
        """Automatically populate rating factors based on the selected period."""
        if self.period_id:
            self.criteria_ids = [(5, 0, 0)]  # Clear existing criteria
            criteria_lines = [
                {
                    'factor_id': form.id,
                }
                for form in self.period_id.form_ids
            ]
            self.criteria_ids = [(0, 0, line) for line in criteria_lines]

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
    
    def action_reject(self):
        for record in self:
            record.state = 'rejected'


class HrPerformanceMeasureCriteria(models.Model):
    _name = "hr.performance.measure.criteria"
    _description = "Performance Evaluation Criteria"

    performance_id = fields.Many2one('hr.performance.measure', string="Performance Measure", required=True, ondelete="cascade")
    factor_id = fields.Many2one('hr.performance.form', string="Rating Factor", required=True, help="The factor being evaluated.")
    factor = fields.Char(string="Factor", compute="_compute_factor", required=True)
    description = fields.Html(string="Description", compute="_compute_description")
    rating = fields.Selection(
        selection=[
            ('5', 'Excellent'),
            ('4', 'Very Good'),
            ('3', 'Good'),
            ('2', 'Average'),
            ('1', 'Poor'),
        ],
        string="Rating",
        required=True,
        help="Rating for this factor."
    )
    score = fields.Float(string="Score", compute="_compute_score", store=True, help="Score derived from the rating.")

    @api.depends('rating')
    def _compute_score(self):
        """Convert the rating to a numeric score."""
        for record in self:
            record.score = int(record.rating) if record.rating else 0
    
    @api.depends('factor_id')
    def _compute_description(self):
        for record in self:
            record.description = record.factor_id.description
    @api.depends('factor_id')
    def _compute_factor(self):
        for record in self:
            record.factor = record.factor_id.name

    @api.constrains('factor_id', 'performance_id')
    def _check_unique_factor(self):
        """Ensure no duplicate factors in an evaluation."""
        for record in self:
            duplicate = self.search([
                ('performance_id', '=', record.performance_id.id),
                ('factor_id', '=', record.factor_id.id),
                ('id', '!=', record.id)
            ])
            if duplicate:
                raise ValidationError("Duplicate rating factors are not allowed in the same evaluation.")
