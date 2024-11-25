from odoo import models, fields


class PerformanceFormTemplate(models.Model):
    _name = "performance.form.template"
    _description = "Performance Form Template"

    name = fields.Char(
        string="Form Name",
        required=True,
        help="The name of the performance evaluation form (e.g., Annual Employee Review).",
    )
    description = fields.Html(
        string="Description",
        sanitize_attributes=False,
        help="A detailed description of the evaluation form.",
    )
    factor_ids = fields.One2many(
        "performance.rating.factor",
        "form_id",
        string="Rating Factors",
        help="The list of performance rating factors included in this form.",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Indicates whether this form template is active and available for use.",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="The order in which this template is displayed in lists.",
    )
