from odoo import models, fields

class DeptProductRequest(models.Model): 
    _name = 'dept.product.request'
    _description = 'Department request for product registration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Product Name", required=True)
    sales_price = fields.Float(string='Sales Price', required=True)
    cost = fields.Float(string='Product Cost')
    description = fields.Text(string='Description Details')
