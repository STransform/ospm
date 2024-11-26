from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrPerformanceEvaluation(models.Model):
    _name = "hr.performance.evaluation"
    _description = "Performance Evaluation"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        "Evaluation Reference", required=True, default=lambda self: _("New")
    )
    schedule_id = fields.Many2one(
        "hr.evaluation.schedule", "Evaluation Schedule", ondelete="cascade"
    )
    employee_id = fields.Many2one(
        "hr.employee", "Employee", required=True, tracking=True
    )
    manager_id = fields.Many2one(
        "hr.employee",
        "Manager",
        compute="_compute_manager_id",
        store=True,
        readonly=True,
    )
    survey_id = fields.Many2one(
        "survey.survey", "Survey Template", required=True, tracking=True
    )
    response_id = fields.Many2one(
        "survey.user_input", "Survey Response", ondelete="set null"
    )

    score = fields.Float("Survey Score", readonly=True, tracking=True)

    evaluation_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
        ],
        default="draft",
        string="Status",
        tracking=True,
    )

    @api.depends("employee_id")
    def _compute_manager_id(self):
        """Automatically assign the manager based on the employee's parent_id."""
        for record in self:
            record.manager_id = (
                record.employee_id.parent_id if record.employee_id else None
            )

    def action_start_evaluation(self):
        """Start the survey for the manager using the survey URL in a new tab."""
        for record in self:
            # Validation: Ensure the manager exists and is linked to a user/partner
            if not record.manager_id:
                raise ValidationError(
                    _("The employee does not have a manager assigned.")
                )
            if (
                not record.manager_id.user_id
                or not record.manager_id.user_id.partner_id
            ):
                raise ValidationError(
                    _(
                        "The manager does not have a linked user/partner to start the survey."
                    )
                )

            # Create and link the survey response
            response = record.survey_id._create_answer(
                survey_id=record.survey_id.id,
                partner_id=record.manager_id.user_id.partner_id.id,
            )
            if not response:
                raise ValidationError(
                    _(
                        "Failed to create a survey response. Please check the survey configuration."
                    )
                )

            record.response_id = response.id
            record.evaluation_status = "in_progress"

            # Generate the URL for the survey
            survey_url = response.get_start_url()

            return {
                "type": "ir.actions.act_url",
                "url": survey_url,
                "target": "new",
            }

    def action_mark_completed(self):
        """Mark the evaluation as completed and calculate the survey score."""
        for record in self:
            # Validation: Ensure the survey is completed
            if not record.response_id or record.response_id.state != 'done':
                raise ValidationError(_("The survey has not been completed. Complete the survey before marking this evaluation as completed."))

            # Fetch the answers from the survey
            answers = self.env['survey.user_input.line'].search([
                ('user_input_id', '=', record.response_id.id)
            ])

            if not answers:
                raise ValidationError(_("No answers found for this survey response."))

            # Map answer values to scores
            score_map = {
                '5': 5,  # Excellent
                '4': 4,  # Very Good
                '3': 3,  # Good
                '2': 2,  # Fine
                '1': 1   # Poor
            }

            total_score = 0
            total_questions = 0

            for answer in answers:
                if answer.value in score_map:
                    total_score += score_map[answer.value]
                    total_questions += 1

            # Calculate average score
            if total_questions > 0:
                record.score = total_score / total_questions
            else:
                record.score = 0

            record.evaluation_status = 'completed'
