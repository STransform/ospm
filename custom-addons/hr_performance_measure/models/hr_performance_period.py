from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class HrPerformancePeriod(models.Model):
    _name = "hr.performance.period"
    _description = "Performance Evaluation Period"

    name = fields.Char(string="Name", required=True, help="Name of the performance period.")
    start_date = fields.Datetime(string="Start Date", required=True, help="The start date of the performance evaluation period.")
    end_date = fields.Datetime(string="End Date", required=True, help="The end date of the performance evaluation period.")
    active = fields.Boolean(
        string="Active", 
        compute="_compute_active", 
        store=False,  # Non-stored field; computed on-the-fly
        help="Indicates if the period is active."
    )
    @api.constrains('start_date', 'end_date')
    def _check_date_constraints(self):
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError("Start Date cannot be later than End Date.")
    @api.model
    def _chech_active(self):
        current_date = datetime.now()
        if self.start_date <= current_date <= self.end_date:
            self.active = True
    
    @api.depends('start_date', 'end_date')
    def _compute_active(self):
        """Compute whether the period is active."""
        current_date = datetime.now()
        if self.start_date and self.end_date:
            self.active = self.start_date <= current_date <= self.end_date
        else:
            self.active = False
        # for record in self:
        #     # Ensure value is explicitly assigned for each record
        #     if record.start_date and record.end_date:
        #         record.active = record.start_date <= current_date <= record.end_date
        #     else:
        #         record.active = False