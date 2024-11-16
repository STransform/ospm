from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrMedicalCostItem(models.Model):
    _name = 'hr.medical.cost.item'
    _description = 'Medical Cost Item'

    coverageId = fields.Many2one('hr.medical.coverage', string="Coverage Request", ondelete="cascade")
    providerType = fields.Selection([
        ('government', 'Government'),
        ('private', 'Private')
    ], string="Provider Type", required=True)
    providerCategory = fields.Selection([
        ('hospital', 'Hospital'),
        ('clinic', 'Clinic'),
        ('pharmacy', 'Pharmacy')
    ], string="Provider Category", required=True)
    date = fields.Datetime(string="Date")
    providerName = fields.Char(string="Provider Name", required=True)
    description = fields.Char(string="Description", required=True)
    amount = fields.Float(string="Amount", required=True)
    
    # Amount Validation  
    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount < 0:
                raise ValidationError("Invalid Input: The Total Requested Amount should be a positive number.")

    @api.onchange('amount')
    def _onchange_amount(self):
        if self.amount < 0:
            return {
                'warning': {
                    'title': 'Invalid Input',
                    'message': 'Amount should be a positive number.',
                }
            }
        
    
    
   
        
        
