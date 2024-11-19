from odoo import models, api, fields
from odoo.exceptions import ValidationError

class HrPerformanceMeasure(models.Model):
    _name = "hr.performance.measure"
    _description = "Performance Measure"

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="The employee being evaluated.")
    contract_id = fields.Many2one('hr.contract', string="Contract", domain="[('employee_id', '=', employee_id)]", required=True, help="Contract associated with the employee.")
    evaluation_period_start = fields.Date(string="Evaluation Start Date", required=True)
    evaluation_period_end = fields.Date(string="Evaluation End Date", required=True)
    evaluation_date = fields.Date(string="Date Evaluated", default=fields.Date.context_today, required=True)
    evaluator_id = fields.Many2one('hr.employee', string="Evaluator", help="The person performing the evaluation.")
    criteria_ids = fields.One2many('hr.performance.measure.criteria', 'performance_measure_id', string="Criteria", help="Criteria to evaluate the performance.")
    total_score = fields.Float(string="Total Score", compute="_compute_total_score", store=True, help="The total score based on criteria ratings.")
    overall_rating = fields.Selection([
        ('excellent', 'Excellent'),
        ('very_good', 'Very Good'),
        ('good', 'Good'),
        ('indifferent', 'Indifferent'),
        ('unsatisfactory', 'Unsatisfactory')
    ], string="Overall Rating", compute="_compute_overall_rating", store=True, help="Overall rating based on the total score.")
    performance_score = fields.Float(string="Performance Score", compute="_compute_performance_score", store=True, help="The calculated performance score.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
    ], default='draft', string="Status", help="The status of the evaluation process.")

    @api.depends('criteria_ids.score')
    def _compute_total_score(self):
        """Compute the total score based on all criteria ratings."""
        for record in self:
            record.total_score = sum(criteria.score for criteria in record.criteria_ids)

    @api.depends('total_score')
    def _compute_overall_rating(self):
        """Compute overall rating based on total score."""
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

    @api.depends('total_score')
    def _compute_performance_score(self):
        """Compute performance score based on the total score."""
        for record in self:
            record.performance_score = record.total_score / len(record.criteria_ids) if record.criteria_ids else 0.0

    def action_submit(self):
        """Submit the evaluation."""
        for record in self:
            if not record.criteria_ids:
                raise ValidationError("Please add at least one performance criterion before submitting.")
            record.state = 'submitted'

    def action_approve(self):
        """Approve the evaluation and apply pay grade increment based on the performance."""
        for record in self:
            if not record.contract_id:
                raise ValidationError("No contract associated with this employee.")
            record.state = 'approved'
            record.contract_id.update_increment_based_on_performance(record.performance_score)

class HrPerformanceMeasureCriteria(models.Model):
    _name = "hr.performance.measure.criteria"
    _description = "Performance Measure Criteria"

    performance_measure_id = fields.Many2one('hr.performance.measure', string="Performance Measure", required=True, ondelete="cascade")
    category = fields.Selection([
        ('personality', 'Personality'),
        ('dependability', 'Dependability'),
        ('job_knowledge', 'Job Knowledge'),
        ('efficiency', 'Efficiency'),
        ('initiative', 'Initiative'),
        ('communication', 'Communication'),
        ('cooperation', 'Cooperation'),
    ], string="Category", required=True, help="The category of the criterion.")
    sub_criteria = fields.Text(string="Sub-Criteria", required=True, help="Detailed description of the sub-criteria.")
    rating = fields.Selection([
        ('5', 'Excellent'),
        ('4', 'Very Good'),
        ('3', 'Good'),
        ('2', 'Indifferent'),
        ('1', 'Unsatisfactory'),
    ], string="Rating", required=True, help="Rating for the criterion.")
    score = fields.Float(string="Score", compute="_compute_score", store=True, help="The score derived from the rating.")

    @api.depends('rating')
    def _compute_score(self):
        """Convert the rating to a numeric score."""
        for record in self:
            record.score = int(record.rating) if record.rating else 0
