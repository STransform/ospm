from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrEvaluationSchedule(models.Model):
    _name = 'hr.evaluation.schedule'
    _description = 'Evaluation Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Schedule Name", required=True, default=lambda self: _('New'))
    survey_id = fields.Many2one('survey.survey', "Survey Template", required=True, tracking=True)
    scheduled_date = fields.Date("Scheduled Date", required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ], default='draft', string="Status", tracking=True)
    evaluations_created = fields.Boolean("Evaluations Created", default=False)

    def action_activate_schedule(self):
        """Activate the schedule and create evaluation records for employees."""
        if not self.env['hr.employee'].search([]):
            raise ValidationError(_("No employees available to evaluate."))

        for employee in self.env['hr.employee'].search([]):
            self.env['hr.performance.evaluation'].create({
                'schedule_id': self.id,
                'employee_id': employee.id,
                'survey_id': self.survey_id.id,
            })
        self.state = 'active'
        self.evaluations_created = True

    def action_close_schedule(self):
        """Close the schedule when evaluations are completed."""
        self.state = 'closed'
