from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrRetirementSettings(models.Model):
    _name = 'hr.retirement.settings'
    _description = 'HR Retirement Settings'
    _rec_name = 'name'

    # Fields
    name =  fields.Char(string="Configuration", default = "Retirement Configuration")
    max_service_years = fields.Integer(string="Maximum Service Years", required=True, default=30)
    retirement_age = fields.Integer(string="Retirement Age", required=True, default=60)
    retirement_threshold_months = fields.Integer(string="Retirement Threshold (Months)", required=True, default=12)