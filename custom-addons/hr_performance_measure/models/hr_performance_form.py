from odoo import fields, models, api
from odoo.exceptions import ValidationError

class HrPerformanceForm(models.Model):
    _name = "hr.performance.form"
    _description = "HR Performance Form"

    name = fields.Char(string="Form Name", required=True, help="Name of the performance form (e.g., Job Performance, Teamwork).")
    description = fields.Text(string="Description", help="Description of the performance form.")
    rating_factors = fields.One2many(
        "hr.performance.form.factor",
        "form_id",
        string="Rating Factors",
        help="List of factors that will be evaluated in this form."
    )
    period_id = fields.Many2one(
        "hr.performance.period",
        string="Evaluation Period",
        help="The evaluation period associated with this form."
    )

    @api.constrains('rating_factors')
    def _check_rating_factors(self):
        """Ensure at least one rating factor is defined for the form."""
        for record in self:
            if not record.rating_factors:
                raise ValidationError("You must add at least one rating factor to the form.")

class HrPerformanceFormFactor(models.Model):
    _name = "hr.performance.form.factor"
    _description = "HR Performance Form Rating Factor"

    name = fields.Char(string="Rating Factor", required=True, help="The factor being evaluated (e.g., Productivity, Attendance).")
    description = fields.Text(string="Description", help="Details about what this factor evaluates.")
    weight = fields.Float(
        string="Weight (%)",
        help="The importance weight of this factor in the overall evaluation (e.g., 20%)."
    )
    form_id = fields.Many2one(
        "hr.performance.form",
        string="Performance Form",
        required=True,
        ondelete="cascade",
        help="The performance form this factor belongs to."
    )

    @api.constrains('weight')
    def _check_weight(self):
        """Ensure the weight is valid (between 0 and 100)."""
        for record in self:
            if record.weight < 0 or record.weight > 100:
                raise ValidationError("The weight must be between 0 and 100.")
