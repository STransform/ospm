from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date

class HrEvaluationSchedule(models.Model):
    _name = 'hr.evaluation.schedule'
    _description = 'Evaluation Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Schedule Name", required=True)
    from_date = fields.Date(string="From", required=True, tracking=True)
    to_date = fields.Date(string="To",required=True, tracking=True)
    survey_id = fields.Many2one('survey.survey', "Survey Template", required=True, tracking=True)
    scheduled_date = fields.Date("Deadline", required=True, tracking=True)
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
        
    
    # validate from to date
    @api.constrains('from_date', 'to_date')
    def _check_dates(self):
        for record in self:
            if record.to_date and record.from_date and record.to_date < record.from_date:
                raise ValidationError("'To' date cannot be earlier than 'From' date.")
    
    
    # close form if it is expired
    # @api.depends('scheduled_date', 'state')
    # def update_status_based_on_deadline(self):
    #     today = date.today()
    #     print("================>", today)
    #     records_to_update = self.search([
    #         ('state', '!=', 'closed'),
    #         ('scheduled_date', '<', today)
    #     ])
    #     for record in records_to_update:
    #         record.state = 'closed'

    