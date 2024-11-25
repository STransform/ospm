from odoo import fields, models


class PromotionType(models.Model):
    """In this custom model requires ,
         we have to specify the promotion type in promotion form """
    _name = 'promotion.type'
    _description = 'Promotion Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'promotion_type'

    promotion_type = fields.Text(string='Promotion Type', help='Promotion type')
