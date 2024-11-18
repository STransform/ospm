from odoo import models, api, fields
from odoo.exceptions import ValidationError

class HrPerformanceMeasure(models.Model):
    _name = "hr.performance.measure"
    _description = "Performance Measure"
    
    