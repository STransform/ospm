from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class EarlyRetirementRequest(models.Model):
    _name = 'hr.early.retirement.request'
    _description = 'Early Retirement Request'

    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env.user.employee_id, readonly=True)
    employee_name = fields.Char(string="Employee", related='employee_id.name', readonly=True)
    department = fields.Char(string="Department", related='employee_id.department_id.name', readonly=True)
    proposed_retirement_date = fields.Date(string="Proposed Retirement Date", required=True)
    request_date = fields.Date(string="Request Submission Date", default=fields.Date.today, readonly=True)
    reason = fields.Text(string="Reason", required=True, help="Provide a justification for early retirement.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Status", default='draft', readonly=True)
    comment = fields.Text(string="Comment")
    user_can_comment = fields.Boolean(string="Can Comment", compute="_compute_user_can_comment", store=False)


    # validation for proposed_retirement_daTruete 
    @api.onchange('proposed_retirement_date')
    def _onchange_proposed_retirement_date(self):
        if self.proposed_retirement_date and self.proposed_retirement_date <= datetime.now().date():
            raise ValidationError("Proposed retirement date cannot be in the past.")
    
    def action_submit(self):
        """Submit the early retirement request."""
        for record in self:
            if record.proposed_retirement_date <= datetime.now().date():
                raise ValidationError("Proposed retirement date cannot be in the past.")
            record.state = 'submitted'
            record.request_date = datetime.today()
    
    def action_approve(self):
        """Approve the early retirement request and deactivate employee access."""
        self.state = 'approved'
        self.employee_id.retirement_date = self.proposed_retirement_date
        self.employee_id.retirement_extended = True

    def action_reject(self):
        """Reject the early retirement request."""
        self.state = 'rejected'


    @api.model
    def _compute_user_can_comment(self):
        for record in self:
            record.user_can_comment = self.env.user.has_group("planning.group_ceo")

    def retire_employee_early(self):
        for record in self:
            if record.state == 'approved' and self.employee_id.retirement_date <= datetime.now().date():
                record.employee_id.near_retirement = False
                record.employee_id.is_retired = True
                if record.employee_id.user_id:
                    record.employee_id.user_id.active = False
                record.employee_id.active = False

    def update_retired_employee_early(self):
        employees = self.search([])
        employees.retire_employee_early()