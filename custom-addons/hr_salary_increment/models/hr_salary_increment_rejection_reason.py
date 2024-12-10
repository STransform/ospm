from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrBonusRejectionWizard(models.TransientModel):
    _name = "hr.salary.increment.batch.rejection.wizard"
    _description = "Salary Increment Rejection Wizard"

    rejection_reason = fields.Text(string="Rejection Reason", required=True)

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
