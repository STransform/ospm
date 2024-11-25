from odoo import fields, models
class PromotionPopup(models.TransientModel):
    _name = 'promotion.popup'
    _description = 'Popup for Editing Employee Profile'

    employee_id = fields.Many2one('hr.employee', string="Employee")

    def action_edit_profile(self):
        """Redirect to the employee profile form view."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Employee Profile',
            'res_model': 'hr.employee',
            'view_mode': 'form',
            'res_id': self.employee_id.id,
            'target': 'current',
        }

    def action_later(self):
        """Close the popup."""
        return {'type': 'ir.actions.act_window_close'}
