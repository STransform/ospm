from odoo import api, models, fields
from odoo.exceptions import ValidationError

class HrPerformanceMeasureCriteria(models.Model):
    _name = "hr.performance.measure.criteria"
    _description = "Performance Evaluation Criteria"
    
    factor_id = fields.Many2one(
        "hr.performance.form",
        string="Rating Factor",
        help="The factor being evaluated.",
    )
    rating = fields.Selection(
        selection=[
            ("5", "Excellent"),
            ("4", "Very Good"),
            ("3", "Good"),
            ("2", "Average"),
            ("1", "Poor"),
        ],
        string="Rating",
        required=True,
        help="Rating for this factor.",
    )
    score = fields.Float(
        string="Score",
        compute="_compute_score",
        store=True,
        help="Score derived from the rating.",
    )
    
    @api.depends("rating")
    def _compute_score(self):
        """Convert the rating to a numeric score."""
        for record in self:
            record.score = int(record.rating) if record.rating else 0
