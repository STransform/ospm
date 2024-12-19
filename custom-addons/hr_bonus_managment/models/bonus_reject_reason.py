from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrBonusRejectionWizard(models.TransientModel):
    _name = "hr.bonus.rejection.wizard"
    _description = "Bonus Rejection Wizard"

    rejection_reason = fields.Text(string="Rejection Reason", required=True)
    # add notification function 
    @api.model
    def send_notification(self, message, user, title, model, res_id):
        self.env["custom.notification"].create(
            {
                "title": title,
                "message": message,
                "user_id": user.id,
                "action_model": model,
                "action_res_id": res_id,
            }
        )


    def confirm_rejection(self):
        """Confirm rejection with a reason."""
        context = dict(self._context or {})
        bonus_id = context.get('active_id')
        if not bonus_id:
            raise ValidationError("No Bonus Batch found to reject.")

        bonus_batch = self.env['hr.bonus.managment'].browse(bonus_id)
        if bonus_batch.state != 'submitted':
            raise ValidationError("Only submitted batches can be rejected.")

        bonus_batch.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })
        ## search users with specific group
        department_manager = self.env.ref("user_group.group_department_manager").users
        title = "Bonus Rejected"
        message = f"rejected."
        for user in department_manager:
            self.send_notification(
                message=message,
                user=user,
                title=title,
                model=self._name,
                res_id=self.id,
            )
            user.notify_success(title=title, message=message)
        self.env.user.notify_success("Bonus Rejected")