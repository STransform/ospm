from odoo import models, fields, api, _

class PromotionMinutes(models.Model):
    _name = 'promotion.minutes'
    _description = 'Promotion Minutes'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    date = fields.Date(string='Date', required=True)
    minute_by = fields.Many2many('hr.employee', string='Minute By', required=True)
    #employee_ids = fields.Many2many('hr.employee',  string='Participants')

    minutes = fields.Text(string='Minutes', required=True)
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this training session.",
    )
    description = fields.Text(string='Description', required=True)
    state = fields.Selection(
        [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ], readonly=True, default='draft'
    )

    def action_approve(self):
        for record in self:
            record.state = 'approved'

    def action_refuse(self):
        for record in self:
            record.state = 'refused'
