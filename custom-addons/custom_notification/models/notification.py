from odoo import models, fields

class Notification(models.Model):
    _name = 'custom.notification'
    _description = 'User Notifications'

    title = fields.Char(string='Title', required=True)
    message = fields.Text(string='Message', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True)
    is_read = fields.Boolean(string='Read', default=False)
    