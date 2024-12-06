from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class HrRetirementExtensionRequest(models.Model):
    _name = 'hr.retirement.extension.request'
    _description = 'Retirement Extension Request'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, default=lambda self: self.env.user.employee_id)
    employee_name = fields.Char(string="Employee", related='employee_id.name', readonly=True)
    extension_reason = fields.Text(string="Extension Reason", required=True)
    extension_period_months = fields.Integer(string="Extension Period (Months)", required=True)
    current_retirement_date = fields.Date(string="Current Retirement Date", required=True, related='employee_id.retirement_date')
    proposed_new_retirement_date = fields.Date(string="Proposed New Retirement Date", compute="_compute_new_retirement_date", store=True)
    request_date = fields.Date(string="Request Submission Date", default=fields.Date.today, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Status", default='draft', readonly=True)
    
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this training session.",
    )
    comment = fields.Text(string="Comment")
    user_can_comment = fields.Boolean(string="Can Comment", compute="_compute_user_can_comment", store=False)



    @api.onchange('employee_id')
    def is_valid_employee(self):
        if not self.employee_id.near_retirement:
            raise ValidationError("You are not allowed applying for the Extending you retirment period.")

    @api.depends('extension_period_months')
    def _compute_new_retirement_date(self):
        for record in self:
            if record.current_retirement_date and record.extension_period_months:
                record.proposed_new_retirement_date = fields.Date.from_string(record.current_retirement_date) + relativedelta(months=record.extension_period_months)

    @api.model
    def _compute_user_can_comment(self):
        for record in self:
            record.user_can_comment = self.env.user.has_group("planning.group_ceo")
    
    
    def action_submit(self):
        """Submit the extension request."""
        self.state = 'submitted'
        self.request_date = fields.Date.today()

    def action_approve(self):
        """Approve the extension request and update the employee's retirement date."""
        self.state = 'approved'
        self.employee_id.retirement_date = self.proposed_new_retirement_date
        self.employee_id.retirement_extended = True

    def action_reject(self):
        """Reject the extension request."""
        self.state = 'rejected'

    @api.constrains('extension_period_months')
    def _check_extension_period(self):
        """Ensure the extension period is valid."""
        if self.extension_period_months <= 0:
            raise ValidationError("The extension period must be greater than 0 months.")
