# hr_medical_coverage.py

from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError

class HrMedicalCoverage(models.Model):
    _name = 'hr.medical.coverage'
    _description = 'Medical Coverage Request'
    _inherit = ['mail.thread']
    _rec_name = 'create_uid'
    _order = 'create_date desc'

    description = fields.Text(string="Description", required=True)
    hr_description = fields.Text(string="Hr Director Description")
    totalRequestedAmount = fields.Float(string="Total Requested Amount", compute="_compute_total_amount", store=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('hr_approved', 'HR Approved'),
        ('hr_rejected', 'HR Rejected'),
        ('finance_approved', 'Finance Approved'),
        ('finance_rejected', 'Finance Rejected')
    ], default='draft', string="Status")

    # Medical Cost List
    costItemIds = fields.One2many('hr.medical.cost.item', 'coverageId', string="Medical Cost Items", required=True)

    # Attachments
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments")

    @api.depends('costItemIds.amount')
    def _compute_total_amount(self):
        for record in self:
            record.totalRequestedAmount = sum(item.amount for item in record.costItemIds)
    
    # Methods for request submission and approvals
    def actionSubmit(self):
        self.status = 'submitted'

    def actionHrApprove(self):
        self.status = 'hr_approved'

    def actionHrReject(self):
        self.status = 'hr_rejected'

    def actionFinanceApprove(self):
        self.status = 'finance_approved'

    def actionFinanceReject(self):
        self.status = 'finance_rejected'
        
    
    # Amount Validation  
    @api.constrains('totalRequestedAmount')
    def _check_total_requested_amount(self):
        for record in self:
            if record.totalRequestedAmount < 1:
                raise ValidationError("Invalid Input: The Total Requested Amount should be a positive number.")

    @api.onchange('totalRequestedAmount')
    def _onchange_total_requested_amount(self):
        if self.totalRequestedAmount < 0:
            return {
                'warning': {
                    'title': 'Invalid Input',
                    'message': 'Amount should be a positive number.',
                }
            }
    
    def write(self, vals):
        # Check if hr_description is being modified
        if 'hr_description' in vals:
            # Check if the current user is in the HR Director group
            if not self.env.user.has_group('hr_medical_coverage.group_hr_director'):
                raise AccessError("You are not allowed to edit the HR Description field.")
        return super(HrMedicalCoverage, self).write(vals)
        
    # Hr description read only
        
        
    # # notification
    # def actionSubmit(self):
    #     self.status = 'submitted'

    #     # Get HR and Finance Officers' user IDs
    #     hr_group = self.env.ref('hr_medical_coverage.group_hr_director')
    #     finance_group = self.env.ref('hr_medical_coverage.group_finance_officer')
    #     user_ids = hr_group.users.ids + finance_group.users.ids

    #     # Send real-time notifications
    #     for user_id in user_ids:
    #         self.env['bus.bus'].sendone(
    #             (self._cr.dbname, 'res.partner', user_id),  # Channel
    #             {
    #                 'type': 'simple_notification',
    #                 'title': ("New Medical Coverage Request"),
    #                 'message': ("A new medical coverage request has been submitted."),
    #                 'sticky': False,  # Set to True if you want the popup to remain visible until manually closed
    #             }
    #         )