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
    
    answer_ids = fields.One2many('hr.performance.evaluation.answer', 'performance_evaluation_id', string="Answers")
    total_score = fields.Float("Total Score", readonly=True, tracking=True)
    all_answers = fields.Text("Recorded Answers", readonly=True)


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
        """Mark the evaluation as completed, store questions and answers, and calculate the total score."""
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

            # Clear existing answers
            record.answer_ids.unlink()

            # Initialize variables to store results
            total_score = 0

            # Process each answer line
            for answer in answers:
                question_text = answer.question_id.display_name or answer.question_id.name
                answer_text = answer.display_name or _('Skipped')
                score = answer.answer_score or 0

                # Create an answer record
                self.env['hr.performance.evaluation.answer'].create({
                    'performance_evaluation_id': record.id,
                    'question': question_text,
                    'answer': answer_text,
                    'score': score,
                })

                # Add the score to the total score
                total_score += score

            # Store the total score in the evaluation record
            record.total_score = total_score

            # Update evaluation status
            record.evaluation_status = 'completed'

            # Log the result for the employee
            record.message_post(
                body=_("Survey completed with a total score of %.2f for %s.") % (
                    record.total_score, record.employee_id.name),
                subtype_id=self.env.ref('mail.mt_note').id
            )
