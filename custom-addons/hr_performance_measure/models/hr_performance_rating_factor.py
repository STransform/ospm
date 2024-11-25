from odoo import fields, models, api
from odoo.exceptions import ValidationError


from odoo import models, fields


class PerformanceRatingFactor(models.Model):
    _name = "performance.rating.factor"
    _description = "Performance Rating Factor"

    name = fields.Char(
        string="Factor Name",
        required=True,
        help="Name of the performance factor being evaluated (e.g., Communication, Teamwork).",
    )
    description = fields.Html(
        string="Factor Description",
        sanitize_attributes=False,
        help="Detailed explanation of the factor being evaluated.",
    )
    answer_ids = fields.One2many(
        "rating.factor.answer",
        "factor_id",
        string="Answer Options",
        help="Predefined answer choices for this factor.",
    )
    form_id = fields.Many2one(
        "performance.form.template",
        string="Performance Form Template",
        ondelete="cascade",
        help="The performance form template this factor is linked to.",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="The order in which this factor is displayed in the performance form.",
    )



class RatingFactorAnswer(models.Model):
    """
    Preconfigured answers for rating factors. This model stores the fixed
    choices (e.g., Excellent, Good) and their associated scores.
    """

    _name = "rating.factor.answer"
    _rec_name = "value"
    _order = "sequence, id"
    _description = "Rating Factor Answer"

    # Related to the rating factor
    factor_id = fields.Many2one(
        "performance.rating.factor",
        string="Rating Factor",
        ondelete="cascade",
        required=True,
        help="The rating factor this answer is linked to.",
    )

    # Answer details
    value = fields.Selection(
        selection=[
            ("5", "Excellent"),
            ("4", "Very Good"),
            ("3", "Good"),
            ("2", "Average"),
            ("1", "Poor"),
        ],
        string="Answer Choice",
        required=True,
        help="The predefined choice for this rating factor.",
    )
    score = fields.Integer(
        string="Score",
        compute="_compute_score",
        store=True,
        help="The numerical score associated with this choice.",
    )

    @api.depends("value")
    def _compute_score(self):
        """Automatically computes the score from the selection value."""
        for record in self:
            record.score = int(record.value) if record.value else 0

