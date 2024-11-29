from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class Training(models.Model):
    _name = 'hr.training'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description= 'Training module main class'


    # char fields
    name = fields.Char(string="Training Name", required=True)

    #date Fields
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)

    # Many to many fields
    trainer = fields.Many2one('hr.employee', string='Trainer', required=True)
    department_id = fields.Many2one('hr.department',  string='Departement', required=True)
    employee_ids = fields.Many2many('hr.employee',  string='Participants')

    # Long Text fields
    description = fields.Text(string='Description')

    # attachement files 
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this training session.",
    )

    #  computed fields
    state = fields.Selection(string='State', selection=[('new', 'New'), ('approved', 'Approved') , ('refused', 'Refused'),('taken', 'Taken')], default="new", store=True)


    # @api.onchange('department_id')
    # def _onchange_department_id(self):
    #     if self.department_id:
    #         self.employee_ids = [(5, 0, 0)]  
    #         return {'domain': {'employee_ids': [('department_id', '=', self.department_id.id)]}}
    #     return {'domain': {'employee_ids': []}}
    
    
    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            # Clear previous selections
            self.employee_ids = [(5, 0, 0)]
            # Set domain to filter employees based on the selected department
            return {'domain': {'employee_ids': [('department_id', '=', self.department_id.id)]}}
        else:
            # If no department is selected, clear the domain
            self.employee_ids = [(5, 0, 0)]
            return {'domain': {'employee_ids': []}}
        
    def action_accepted(self):
        for record in self:
            record.state = 'approved'
            # Notify all users in the system

            # if record.created_by:
            # Send a danger notification to the creator
            record.created_by.notify_success("Training is Accepted by CEO", sticky=True)
            #    if record.created_by:
            #             message = _('Training %s has been approved') % record.name
            #             self._notify_creator(record.created_by, message, title='Training Approved')  
            # channel = ('otechenterprise', 'res.partner', record.created_by.partner_id.id)
            # message = {
            #     'title': 'Training Approved',
            #     'body': f'The training "{record.name}" has been approved.',
            #     'sticky': False
            # }
            # self.env['bus.bus']._sendone(channel, 'notify_info', message)   

    def action_refused(self):
        for record in self:
            record.state = 'refused'
            record.created_by.notify_danger("Training is refused by CEO", sticky=True)

    def actions_taken(self):
        for record in self:
            record.state = 'taken'


    @api.model
    def get_data(self):
        refused_training = self.search([('state', '=', 'refused')])
        accepted_training = self.search([('state', '=', 'approved')])
        taken_training =  self.search([('state', '=', 'taken')])

        return {
            'refused': len(refused_training),
            'accepted': len(accepted_training),
            'taken': len(taken_training)
        }
