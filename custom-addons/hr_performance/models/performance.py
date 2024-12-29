from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class HrPerformanceEvaluation(models.Model):
    _name = "hr.performance.evaluation"
    _description = "Performance Evaluation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "employee_id"
    _order = "create_date desc"

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
    employee_comment = fields.Text("Employee Comment or Sign on")

    evaluation_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("employee_review", "Employee Review"),
            ("employee_rejected", "Employee Rejected"),
            ("employee_accepted", "Employee Accepted"),
            ("completed", "Completed"),
        ],
        default="draft",
        string="Status",
        tracking=True,
    )

    answer_ids = fields.One2many(
        "hr.performance.evaluation.answer",
        "performance_evaluation_id",
        string="Answers",
    )
    total_score = fields.Float("Total Score", readonly=True, tracking=True)
    all_answers = fields.Text("Recorded Answers", readonly=True)

    is_employee = fields.Boolean(compute="_compute_is_employee")
    is_manager = fields.Boolean(compute="_compute_is_manager")
    is_manager_to_employee = fields.Boolean(compute="_compute_is_manager_to_employee")
    is_manager_start = fields.Boolean(compute="_compute_is_manager_start")

    score_category = fields.Selection(
        [
            ("below_75", "Below 75"),
            ("75_to_84", "75 - 84"),
            ("85_to_94", "85 - 94"),
            ("95_above", "95 and Above"),
        ],
        string="Score Category",
        compute="_compute_score_category",
        store=True,
    )

    @api.depends("total_score")
    def _compute_score_category(self):
        for record in self:
            if record.total_score >= 95:
                record.score_category = "95_above"
            elif record.total_score >= 85:
                record.score_category = "85_to_94"
            elif record.total_score >= 75:
                record.score_category = "75_to_84"
            else:
                record.score_category = "below_75"

    @api.depends("employee_id", "employee_id.user_id")
    def _compute_is_employee(self):
        for record in self:
            record.is_employee = record.employee_id.user_id.id == self.env.uid

    def _compute_is_manager(self):
        for record in self:
            record.is_manager = (
                record.employee_id.parent_id.user_id.id == self.env.uid
                and record.evaluation_status == "employee_accepted"
            )

    def _compute_is_manager_start(self):
        for record in self:
            record.is_manager_start = (
                record.employee_id.parent_id.user_id.id == self.env.uid
                and record.evaluation_status == "draft"
            )

    def _compute_is_manager_to_employee(self):
        for record in self:
            record.is_manager_to_employee = (
                record.employee_id.parent_id.user_id.id == self.env.uid
                and record.evaluation_status == "in_progress"
            )

    @api.depends("employee_id")
    def _compute_manager_id(self):
        """Automatically assign the manager based on the employee's parent_id."""
        for record in self:
            record.manager_id = (
                record.employee_id.parent_id if record.employee_id else None
            )
            
    # notification function
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

    def action_start_evaluation(self):
        """Start the survey for the manager using the survey URL in a new tab."""
        for record in self:
            if record.evaluation_status != "draft":
                raise ValidationError(
                    _("The evaluation is already started or completed.")
                )

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
            if (
                record.schedule_id.state == "closed"
                or record.schedule_id.scheduled_date < fields.Date.today()
            ):
                raise ValidationError(
                    "The Form is either closed or expiered! please conctact Hr Director"
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

            survey_url = response.get_start_url()
            return {
                "type": "ir.actions.act_url",
                "url": survey_url,
                "target": "new",
            }

    def action_submit_to_employee(self):
        """Submit the evaluation for employee review."""
        for record in self:
            if record.evaluation_status != "in_progress":
                raise ValidationError(
                    _("You can only submit evaluations that are in progress.")
                )

            if not record.response_id or record.response_id.state != "done":
                raise ValidationError(
                    _("The survey must be completed before submission.")
                )

            # Fetch the answers from the survey
            answers = self.env["survey.user_input.line"].search(
                [("user_input_id", "=", record.response_id.id)]
            )

            if not answers:
                raise ValidationError(_("No answers found for this survey response."))

            # Clear existing answers
            record.answer_ids.unlink()

            # Initialize variables to store results
            total_score = 0
            length = 0

            # Process each answer line
            for answer in answers:
                question_text = (
                    answer.question_id.display_name or answer.question_id.name
                )
                answer_text = answer.display_name or _("Skipped")
                score = answer.answer_score or 0

                # Create an answer record
                self.env["hr.performance.evaluation.answer"].create(
                    {
                        "performance_evaluation_id": record.id,
                        "question": question_text,
                        "answer": answer_text,
                        "score": score,
                    }
                )

                # Add the score to the total score
                temp = answer_text
                if not answer_text == "Skipped":
                    temp = eval((answer_text))
                else:
                    temp = 0
                total_score += temp
                length += 1

            # Store the total score in the evaluation record
            curr = 0
            if length > 0:
                curr = length * 5
                total_score = total_score * 100 / curr

            record.total_score = total_score

            record.evaluation_status = "employee_review"
            # send notification to employee
            self.send_notification(
                message="Your evaluation is completed Please Accept it!",
                user=record.employee_id.user_id,
                title="Evaluation Completed",
                model=self._name,
                res_id=self.id,
            )

    def action_employee_reject(self):
        # emplooyee reject
        for record in self:
            if record.evaluation_status != "employee_review":
                raise ValidationError(_("You can only reject after review"))
            record.evaluation_status = "employee_rejected"
           

    def action_employee_accept(self):
        # emplooyee reject
        for record in self:
            if record.evaluation_status != "employee_review":
                raise ValidationError(_("You can only accept after review"))
            record.evaluation_status = "employee_accepted"

    def action_submit_to_hr(self):
        """Submit the evaluation to HR."""
        for record in self:
            if record.evaluation_status != "employee_accepted":
                raise ValidationError(
                    _("You can only submit evaluations after employee review.")
                )

            record.evaluation_status = "submitted_to_hr"
            # send notification to hr 
            hr_group = self.env.ref("user_group.group_hr_office")
            for user in hr_group.users:
                self.send_notification(
                    message="Evaluation Accepted by Employee Submitted ",
                    user=user,
                    title="Evaluation Submitted",
                    model=self._name,
                    res_id=self.id,
                )

    def action_mark_completed(self):
        """Mark the evaluation as completed, store questions and answers, and calculate the total score."""
        for record in self:
            # Validation: Ensure the survey is completed
            if not record.response_id or record.response_id.state != "done":
                raise ValidationError(
                    _(
                        "The survey has not been completed. Complete the survey before marking this evaluation as completed."
                    )
                )

            # Update evaluation status
            record.evaluation_status = "completed"

            # Log the result for the employee
            record.message_post(
                body=_("Survey completed with a total score of %.2f for %s.")
                % (record.total_score, record.employee_id.name),
                subtype_id=self.env.ref("mail.mt_note").id,
            )
