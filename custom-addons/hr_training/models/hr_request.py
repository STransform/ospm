from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
class HrTrainingRequest(models.Model):
    _name = 'hrtraining.request'
    _description = 'HR Training Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Request Name", required=True)
    training_programs = fields.One2many('hrtraining.program', 'training_id', string='Training Programs')
    description = fields.Text(string='Description')
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this training session.",
    )

    state_by_ceo = fields.Selection([
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ])

    state_by_planning = fields.Selection([
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ])

    combined_state = fields.Selection([
        ('approved', 'Approved'),
        ('refused', 'Rejected'),
        ('pending', 'Pending'),
    ], string="Combined State", compute='_compute_combined_state')
 


    state = fields.Selection(
        string='State',
        selection=[('pending', 'Pending'), ('approved', 'Approved'), ('refused', 'Refused')],
        default='pending',
        store=True,
    )

    @api.depends('state_by_ceo', 'state_by_planning')
    def _compute_combined_state(self):
        for record in self:
            if 'refused' in [record.state_by_planning, record.state_by_ceo]:
                record.combined_state = 'refused'
            elif all(state == 'approved' for state in [record.state_by_planning, record.state_by_ceo]):
                record.combined_state = 'approved'
            else:
                record.combined_state = 'pending'


    def action_approve_ceo(self):
        for record in self:
            record.state_by_ceo = 'approved'

    def action_reject_ceo(self):
        for record in self:
            record.state_by_ceo = 'refused'

    def action_approve_planning(self):
        for record in self:
            record.state_by_planning = 'approved'

    def action_reject_planning(self):
        for record in self:
            record.state_by_planning = 'refused'
