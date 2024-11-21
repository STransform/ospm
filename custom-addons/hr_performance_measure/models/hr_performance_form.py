from odoo import fields, models, api
from odoo.exceptions import ValidationError

class HrPerformanceForm(models.Model):
    _name = "hr.performance.form"
    _description = "HR Performance Form"

    name = fields.Char(string="Form Name", required=True, help="Name of the performance form (e.g., Job Performance, Teamwork).")
    description = fields.Html(string='Job Description', sanitize_attributes=False)