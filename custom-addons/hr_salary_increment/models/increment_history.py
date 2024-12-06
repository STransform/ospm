from odoo import fields, models, api

class HrSalaryIncrementHistory(models.Model):
    _name = "hr.salary.increment.history"
    _description = "Salary Increment History of Employees"
    _order = "create_date desc"

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, ondelete='cascade')
    increment_date = fields.Datetime(string="Increment Date", default=fields.Datetime.now, required=True)
    approved_by = fields.Many2one('res.users', string="Approved By", required=True, default=lambda self: self.env.user)
    from_increment_name = fields.Char(string="From Increment")
    to_increment_name = fields.Char(string="To Increment")