from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
class DeptRequest(models.Model):
    _name = 'dept.request'
    _description = 'Department Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Request Name", required=True)
    training_programs = fields.One2many('training.program', 'training_id', string='Training Programs')
    description = fields.Text(string='Description')
    department_id = fields.Many2one('hr.department', string='Department', required=True, readonly=True, default=lambda self: self._get_default_department())
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this training session.",
        required=True,
    )

    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),('requested', 'Approval Requested'), ('approved', 'Approved'), ('refused', 'Refused')],
        default='draft',
        store=True,
    )

    @api.model
    def _get_default_department(self):
        """Fetch the department of the currently logged-in user."""
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if not employee or not employee.department_id:
            raise UserError("No department is assigned to the current user.")
        return employee.department_id.id
    
    def action_request_approval(self):
        for record in self:
            record.state = 'requested'

    def action_approve_request(self):
        for record in self:
            record.state = 'approved'

    def action_refuse_request(self):
        for record in self:
            record.state = 'refused'