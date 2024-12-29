from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrBonusRejectionWizard(models.TransientModel):
    _name = "hr.salary.increment.batch.rejection.wizard"
    _description = "Salary Increment Rejection Wizard"

    rejection_reason = fields.Text(string="Rejection Reason", required=True)
    
    # send notification function
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
        increment_id = context.get('active_id')
        if not increment_id:
            raise ValidationError("No Salary Inrement Batch found to reject.")

        increment_batch = self.env['hr.salary.increment.batch'].browse(increment_id)
        if increment_batch.state != 'submitted':
            raise ValidationError("Only submitted batches can be rejected.")

        increment_batch.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })
        # send notification to hr office
        hr_office = self.env.ref("user_group.group_hr_office").users
        for user in hr_office:
            self.send_notification(
                message="Salary Increment Request Rejected",
                user=user,
                title="Salary Increment Request",
                model=self._name,
                res_id=self.id,
            )
            # web notify
            user.notify_danger("Salary Increment Request Rejected")
        self.env.user.notify_danger("Salary Increment Request Rejected")
