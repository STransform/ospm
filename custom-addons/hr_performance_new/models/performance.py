from odoo import models, fields, api

class PerformanceMeasure(models.Model):
    _name = 'hr.performance.measure'
    _description = 'Employee Performance Measure'

    name = fields.Char("Name", required=True)
    employee_id = fields.Many2one('hr.employee', "Employee", required=True)
    manager_id = fields.Many2one(
        'hr.employee', 
        "Manager", 
        related='employee_id.parent_id', 
        store=True, 
        readonly=True
    )
    survey_id = fields.Many2one('survey.survey', "Survey Template", required=True)
    evaluation_status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], default='pending', string="Status")
    response_count = fields.Integer(
        "Responses", 
        compute='_compute_response_count', 
        store=False
    )

    @api.depends('survey_id')
    def _compute_response_count(self):
        for record in self:
            responses = self.env['survey.user_input'].search([
                ('survey_id', '=', record.survey_id.id),
                ('state', '=', 'done'),
            ])
            record.response_count = len(responses)

    def action_send_survey(self):
        for record in self:
            if record.manager_id and record.survey_id:
                user_input = self.env['survey.user_input'].create({
                    'survey_id': record.survey_id.id,
                    'partner_id': record.manager_id.user_id.partner_id.id,
                    'state': 'new',
                })
                record.survey_id.action_send_survey(
                    partner_ids=[record.manager_id.user_id.partner_id.id],
                    context={
                        'default_res_model': 'hr.performance.measure',
                        'default_res_id': record.id,
                        'force_send': True,
                    }
                )
                record.evaluation_status = 'in_progress'

    def action_view_responses(self):
        self.ensure_one()
        return {
            'name': 'Survey Responses',
            'view_mode': 'tree,form',
            'res_model': 'survey.user_input',
            'type': 'ir.actions.act_window',
            'domain': [('survey_id', '=', self.survey_id.id)],
        }
