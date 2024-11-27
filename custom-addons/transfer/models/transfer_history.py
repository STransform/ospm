from odoo import fields, models, api

class TransferHistory(models.Model):
    _name = "transfer.history"
    _description = "Transfer History of Employees"

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, ondelete='cascade')
    transfer_date = fields.Datetime(string="Transfer Date", default=fields.Datetime.now, required=True)
    from_department_id = fields.Many2one('hr.department', string="From Department", required=True)
    to_department_id = fields.Many2one('hr.department', string="To Department", required=True)
    from_position_id = fields.Many2one('hr.job', string="From Position", required=True)
    to_position_id = fields.Many2one('hr.job', string="To Position", required=True)
    reason = fields.Text(string="Reason for Transfer")
    approved_by = fields.Many2one('res.users', string="Approved By", required=True, default=lambda self: self.env.user)
    from_department_name = fields.Char(string="From Department", related='from_department_id.name')
    to_department_name = fields.Char(string="To Department", related='to_department_id.name')