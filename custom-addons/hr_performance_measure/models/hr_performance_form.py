from odoo import fields, models, api
from odoo.exceptions import ValidationError

class HrPerformanceForm(models.Model):
    _name = "hr.performance.form"
    _description = "HR Performance Form"

    name = fields.Char(string="Form Name", required=True, help="Name of the performance form (e.g., Job Performance, Teamwork).")
    rating_factors = fields.One2many(
        "hr.performance.form.factor",
        "form_id",
        string="Rating Factors",
        help="List of factors that will be evaluated in this form."
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