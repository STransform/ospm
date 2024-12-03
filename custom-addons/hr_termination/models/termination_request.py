from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TerminationRequest(models.Model):
    _name = 'termination.request'
    _description = 'Termination Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Request Name",
        required=True,
        readonly=True,
        default="New"
    )
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self._get_employee(), readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id', store=True)
    manager_id = fields.Many2one('hr.employee', string='Manager', related='employee_id.parent_id', store=True)
    termination_date = fields.Date(string='Termination Date', required=True)
    reason = fields.Text(string='Reason', required=True)
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'), ('requested', 'Approval Requested'), ('approved', 'Approved'), ('refused', 'Refused')],
        default='draft',
        store=True,
    )
    job_id = fields.Many2one('hr.job', string='Job Position', related='employee_id.job_id', store=True)
    state_by_service = fields.Selection(
        string='State by Manager',
        selection=[('approved', 'Approved'), ('refused', 'Refused')],
        store=True,
    )
    state_by_director = fields.Selection(
        string='State by Director',
        selection=[('approved', 'Approved'), ('refused', 'Refused')],
        store=True,
    )
    state_by_dceo = fields.Selection(
        string='State by DCEO',
        selection=[('approved', 'Approved'), ('refused', 'Refused')],
        store=True,
    )
    state_by_ceo = fields.Selection(
        string='State by CEO',
        selection=[('approved', 'Approved'), ('refused', 'Refused')],
        store=True,
    )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            if not employee:
                raise UserError("No employee is assigned to the current user.")
            
            new_name = f"Termination Request for {employee.name}"
            vals['name'] = new_name
        return super(TerminationRequest, self).create(vals)
    
    def _get_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)



    def action_by_service_request_approval(self):
        for record in self:
            record.state_by_service = 'approved'

    def action_by_service_refuse_request(self):
        for record in self:
            record.state_by_service = 'refused'

    def action_by_director_request_approval(self):
        for record in self:
            record.state_by_director = 'approved'
    
    def action_by_director_refuse_request(self):
        for record in self:
            record.state_by_director = 'refused'
    
    def action_by_dceo_request_approval(self):
        for record in self:
            record.state_by_dceo = 'approved'

    def action_by_dceo_refuse_request(self):
        for record in self:
            record.state_by_dceo = 'refused'
    
    def action_by_ceo_request_approval(self):
        for record in self:
            record.state_by_ceo = 'approved'
    
    def action_by_ceo_refuse_request(self):
        for record in self:
            record.state_by_ceo = 'refused'


