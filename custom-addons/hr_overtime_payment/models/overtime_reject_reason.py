from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrBonusRejectionWizard(models.TransientModel):
    _name = "hr.overtime.payment.rejection.wizard"
    _description = "Overtime Payment Rejection Wizard"

    rejection_reason = fields.Text(string="Rejection Reason", required=True)

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
