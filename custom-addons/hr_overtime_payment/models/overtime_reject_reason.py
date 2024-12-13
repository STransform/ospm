from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrBonusRejectionWizard(models.TransientModel):
    _name = "hr.overtime.payment.rejection.wizard"
    _description = "Overtime Payment Rejection Wizard"

    rejection_reason = fields.Text(string="Rejection Reason", required=True)
     # add notification function 
    @api.model
    def send_notification(self, message, user, title):
        self.env['custom.notification'].create({
            'title': title,
            'message': message,
            'user_id': user.id,
        })
    def confirm_rejection(self):
        """Confirm rejection with a reason."""
        context = dict(self._context or {})
        overtime_id = context.get('active_id')
        if not overtime_id:
            raise ValidationError("No Overtime Payment found to reject.")

        overtime_payment = self.env['hr.overtime.payment'].browse(overtime_id)
        if overtime_payment.state != 'submitted':
            raise ValidationError("Only submitted Request can be rejected.")

        overtime_payment.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })
        
        
        ## search users with specific group
        department_manager = self.env.ref("user_group.group_department_manager").users
        title = "Overtime Payment Rejected"
        message = f"Rejected."
        for user in department_manager:
            self.send_notification(message, user, title) 
            user.notify_danger(title=title, message=message)
        self.env.user.notify_danger("Request Successfully Rejected")
        
