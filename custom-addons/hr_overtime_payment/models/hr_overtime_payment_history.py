from odoo import fields, models, api

class HrSalaryIncrementHistory(models.Model):
    _name = "hr.overtime.payment.history"
    _description = "Overtime Payment History of Employees"
    _order = "create_date desc"

    
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, ondelete='cascade')
    reference = fields.Many2one('hr.overtime.payment', string="Refernece", required=True, ondelete='cascade')
    overtime_approved_date = fields.Datetime(string="Overtime Payment Approved Date", default=fields.Datetime.now, required=True)
    approved_by = fields.Many2one('res.users', string="Approved By", required=True, default=lambda self: self.env.user)
    overtime_amount = fields.Float(string="Amount", required=True)