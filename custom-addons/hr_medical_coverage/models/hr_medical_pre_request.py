from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError

class HrMedicalPreRequest(models.Model):
    _name = "hr.medical.pre.request"
    _description = "Medical Pre Request"
    _rec_name = "create_uid"
    _order = "create_date desc"
    
    
    description = fields.Text(string="Description", required=True)
    hr_comment = fields.Text(string="Hr Comment")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('hr_rejected', 'Hr Rejected'),
        ('hr_approved', 'Hr Approved')
    ], default='draft', string="Status")
    
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments")
    
    
    def actionSubmit(self):
        self.status = 'submitted'
        
    def actionHrApprove(self):
        self.status = 'hr_approved'

    def actionHrReject(self):
        self.status = 'hr_rejected'
        

    def write(self, vals):
        if 'hr_comment' in vals:
            if not self.env.user.has_group('hr_medical_coverage.group_hr_director'):
                raise AccessError("You are not allowed to edit this field")
        return super(HrMedicalPreRequest, self).write(vals)
    