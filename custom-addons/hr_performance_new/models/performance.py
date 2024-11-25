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
        """Mark the evaluation as completed."""
        if self.evaluation_status != "in_progress":
            raise ValidationError(
                _("The evaluation must be in progress to mark it as completed.")
            )
        self.evaluation_status = "completed"
