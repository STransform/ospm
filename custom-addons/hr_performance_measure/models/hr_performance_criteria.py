from odoo import api, models, fields
from odoo.exceptions import ValidationError

class HrPerformanceMeasureCriteria(models.Model):
    _name = "hr.performance.measure.criteria"
    _description = "Performance Evaluation Criteria"

    performance_id = fields.Many2one(
        "hr.performance.measure",
        string="Performance Measure",
        required=True,
        ondelete="cascade",
    )
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
    
    # description = fields.Html(string="description", compute="_compute_descrioption", store=True)
        
    
    # @api.depends('factor_id')
    # def _compute_descrioption(self):
    #     for record in self:
    #         record.description = record.factor_id.description
    @api.depends("rating")
    def _compute_score(self):
        print("================================", self.factor_id.description)
        """Convert the rating to a numeric score."""
        for record in self:
            record.score = int(record.rating) if record.rating else 0

    # @api.constrains("factor_id", "performance_id")
    # def _check_unique_factor(self):
    #     """Ensure no duplicate factors in an evaluation."""
    #     for record in self:
    #         duplicate = self.search(
    #             [
    #                 ("performance_id", "=", record.performance_id.id),
    #                 ("factor_id", "=", record.factor_id.id),
    #                 ("id", "!=", record.id),
    #             ]
    #         )
    #         if duplicate:
    #             raise ValidationError(
    #                 "Duplicate rating factors are not allowed in the same evaluation."
    #             )
