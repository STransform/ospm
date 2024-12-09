from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrBonusRejectionWizard(models.TransientModel):
    _name = "hr.bonus.rejection.wizard"
    _description = "Bonus Rejection Wizard"

    rejection_reason = fields.Text(string="Rejection Reason", required=True)

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
