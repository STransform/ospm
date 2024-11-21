from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class HrPerformancePeriod(models.Model):
    _name = "hr.performance.period"
    _description = "Performance Evaluation Period"

    name = fields.Char(string="Name", required=True, help="Name of the performance period.")
    assessment_start_date = fields.Datetime(string="Assessment Period From", required=True, help="The start date of the performance evaluation period.")
    assessment_end_date = fields.Datetime(string="Assessment Period To", required=True, help="The end date of the performance evaluation period.")
    form_activation_start_date = fields.Datetime(string="Assessment Start Date", required=True, help="The start date of the performance evaluation period.")
    form_activation_end_date = fields.Datetime(string="Assessment  End Date", required=True, help="The end date of the performance evaluation period.")
    form_ids = fields.Many2many('hr.performance.form', string="Rating Foctars")
    active = fields.Boolean(
        string="Active", 
        compute="_compute_active", 
        store=False,  # Non-stored field; computed on-the-fly
        help="Indicates if the period is currently active."
    )

    @api.constrains('assessment_start_date', 'assessment_end_date', 'form_activation_start_date', 'form_activation_end_date')
    def _check_date_constraints(self):
        for record in self:
            if record.assessment_start_date > record.assessment_end_date or record.form_activation_start_date > record.form_activation_end_date:
                raise ValidationError("Start Date cannot be later than End Date.")
            

    @api.depends('assessment_start_date', 'assessment_end_date')
    def _compute_active(self):
        current_date = datetime.now()
        for record in self:
            # Check if the current date falls within the period
            if record.assessment_start_date and record.assessment_end_date:
                record.active = record.assessment_start_date <= current_date <= record.assessment_end_date
            else:
                record.active = False
