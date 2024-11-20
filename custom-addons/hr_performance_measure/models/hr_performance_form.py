from odoo import fields, models, api
from odoo.exceptions import ValidationError

class HrPerformanceForm(models.Model):
    _name = "hr.performance.form"
    _description = "Hr Performance Form"
    
    name = fields.Char(string="Rating Factor", required=True)
    description = fields.Text(string="Rating Factors Descriptions Lists", required=True)
    
    
    