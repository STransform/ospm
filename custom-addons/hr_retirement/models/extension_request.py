from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from datetime import date

class HrRetirementExtensionRequest(models.Model):
    _name = 'hr.retirement.extension.request'
    _description = 'Retirement Extension Request'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    employee_department = fields.Char(string="Department", compute='_compute_employee_information', readonly=True)
    user_id = fields.Many2one('res.users', string="Requested By", readonly=True)
    extension_reason = fields.Text(string="Extension Reason", required=True)
    extension_period_months = fields.Integer(string="Extension Period (Months)", required=True)
    current_retirement_date = fields.Date(string="Current Retirement Date", required=True, compute='_compute_employee_information')
    proposed_new_retirement_date = fields.Date(string="Proposed New Retirement Date", compute="_compute_new_retirement_date", store=True)
    request_date = fields.Date(string="Request Submission Date", default=fields.Date.today, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Status", default='draft', readonly=True)
    
    employee_state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Employee Status", default='pending', readonly=True)

    comment = fields.Text(string="Comment")
    user_can_comment = fields.Boolean(string="Can Comment", compute="_compute_user_can_comment", store=False)

    @api.depends('employee_id')
    def _compute_employee_information(self):
        for record in self:
            if not record._origin and record.employee_id and not self.employee_id.near_retirement:
                raise ValidationError("The employee is not allowed for the Extending the retirment period.")
            if record.employee_id:
                if record.employee_id.user_id:
                    raise ValidationError("The employee Doesn't Have a related User Account. Please Add User Account for the Employee")
                record.employee_department = record.employee_id.department_id.name
                record.current_retirement_date = record.employee_id.retirement_date
                record.user_id = record.employee_id.user_id.id
            else:
                record.employee_department = False
                record.current_retirement_date = False

    @api.depends('extension_period_months')
    def _compute_new_retirement_date(self):
        for record in self:
            if record.current_retirement_date and record.extension_period_months:
                record.proposed_new_retirement_date = fields.Date.from_string(record.current_retirement_date) + relativedelta(months=record.extension_period_months)

    @api.onchange('extension_period_months')
    def _onchange_extension_period_months(self):
        if self.extension_period_months <= 0:
            raise ValidationError("The extension period must be greater than 0 months.")

    @api.model
    def _compute_user_can_comment(self):
        for record in self:
            record.user_can_comment = self.env.user.id == record.employee_id.user_id.id
    
    
    def action_submit(self):
        """Submit the extension request."""
        self.state = 'submitted'
        self.request_date = fields.Date.today()

    def action_approve(self):
        """Approve the extension request and update the employee's retirement date."""
        retirement_threshold = self.env['hr.retirement.settings'].sudo().search([], limit=1).retirement_threshold_months
        near_retirement = date.today() >= self.proposed_new_retirement_date - relativedelta(months=retirement_threshold)
        self.state = 'approved'
        self.employee_state = 'approved'
        self.sudo().employee_id.write({
            'retirement_extended': True,
            'retirement_date': self.proposed_new_retirement_date,
            'near_retirement' : near_retirement
        })

    def action_reject(self):
        """Reject the extension request."""
        self.state = 'rejected'
        self.employee_state = 'rejected'

    @api.constrains('extension_period_months')
    def _check_extension_period(self):
        """Ensure the extension period is valid."""
        if self.extension_period_months <= 0:
            raise ValidationError("The extension period must be greater than 0 months.")
