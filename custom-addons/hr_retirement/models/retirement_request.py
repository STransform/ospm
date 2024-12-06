from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class HrRetirementRequest(models.Model):
    _name = 'hr.retirement.request'
    _description = 'Retirement Request'

    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env.user.employee_id, readonly=True)
    department = fields.Char(string="Department", related='employee_id.department_id.name', readonly=True)
    proposed_retirement_date = fields.Date(string="Proposed Retirement Date", default = lambda self: self.env.user.employee_id.retirement_date, readonly=True)
    request_date = fields.Date(string="Request Submission Date", default=fields.Date.today(), readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Status", default='draft', readonly=True)
    comment = fields.Text(string="Comment")
    user_can_comment = fields.Boolean(string="Can Comment", compute="_compute_user_can_comment", store=False)



    @api.model
    def _compute_user_can_comment(self):
        for record in self:
            record.user_can_comment = self.env.user.has_group("planning.group_ceo")

    @api.onchange('employee_id')
    def is_valid_employee(self):
        if not self.employee_id.near_retirement:
            raise ValidationError("You are not Allowed To Request for retirement. Please consider requesting for Early retirement")

    
    def action_submit(self):
        """Submit the retirement request."""
        self.state = 'submitted'
        self.request_date = datetime.today()

    def action_approve(self):
        """Approve the retirement request and deactivate employee access."""
        self.state = 'approved'

    def action_reject(self):
        """Reject the retirement request."""
        self.state = 'rejected'
    

    def update_retired_employee(self):
        employees = self.search([])
        employees.retire_employee()  

    def retire_employee(self):
        for record in self:
            if record.state == 'approved' and record.employee_id.retirement_date <= datetime.now().date():
                record.employee_id.near_retirement = False
                record.employee_id.is_retired = True
                if record.employee_id.user_id:
                    record.employee_id.user_id.active = False 
                record.employee_id.active = False
