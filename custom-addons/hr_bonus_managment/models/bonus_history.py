from odoo import fields, models, api

class HrSalaryIncrementHistory(models.Model):
    _name = "hr.bonus.history"
    _description = "Bonus History of Employees"
    _order = "create_date desc"

    
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, ondelete='cascade')
    reference = fields.Many2one('hr.bonus.managment', string="Refernece", required=True, ondelete='cascade')
    bonus_approved_date = fields.Datetime(string="Bonus Approved Date", default=fields.Datetime.now, required=True)
    approved_by = fields.Many2one('res.users', string="Approved By", required=True, default=lambda self: self.env.user)
    bonus_amount = fields.Float(string="Bonus Amount", required=True)