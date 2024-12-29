from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date


class HrEvaluationSchedule(models.Model):
    _name = "hr.evaluation.schedule"
    _description = "Evaluation Schedule"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        "Schedule Name", compute="_compute_name", required=True, readonly=True
    )
    from_date = fields.Date(string="From", required=True, tracking=True)
    to_date = fields.Date(string="To", required=True, tracking=True)
    survey_id = fields.Many2one(
        "survey.survey", "Survey Template", required=True, tracking=True
    )
    scheduled_date = fields.Date("Deadline", required=True, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("closed", "Closed"),
        ],
        default="draft",
        string="Status",
        tracking=True,
    )
    evaluations_created = fields.Boolean("Evaluations Created", default=False)

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

    @api.depends("from_date", "to_date")
    def _compute_name(self):
        for record in self:
            record.name = (
                f"Performance Evaulation from {record.from_date.month}/{record.from_date.year} to {record.to_date.month}/{record.to_date.year} ({self.diff_month(record.from_date, record.to_date)}) months"
                if record.from_date and record.to_date
                else "Performance Evaulation from"
            )

    # month calculation
    def diff_month(self, date1, date2):
        return (date2.year - date1.year) * 12 + date2.month - date1.month

    def action_activate_schedule(self):
        """Activate the schedule and create evaluation records for employees."""
        if not self.env["hr.employee"].search([]):
            raise ValidationError(_("No employees available to evaluate."))

        for employee in self.env["hr.employee"].search([]):
            evaulation = self.env["hr.performance.evaluation"].create(
                {
                    "schedule_id": self.id,
                    "employee_id": employee.id,
                    "survey_id": self.survey_id.id,
                }
            )
            print(evaulation.id)

            if employee.parent_id.user_id:
                message = f"New Performance Evaluation to be submitted for Employee {employee.name}"
                title = "New Performance Evaluation to be submitted"
                self.send_notification(
                    message=message,
                    user=employee.parent_id.user_id,
                    title=title,
                    model="hr.performance.evaluation",
                    res_id=evaulation.id,
                )
                # web notify
                employee.parent_id.user_id.notify_success(title=title, message=message)
        # web notify use evaulation is created
        self.env.user.notify_success("Evaulation is created")
        self.state = "active"
        self.evaluations_created = True

    def action_close_schedule(self):
        """Close the schedule when evaluations are completed."""
        self.state = "closed"

    # validate from to date
    @api.constrains("from_date", "to_date")
    def _check_dates(self):
        for record in self:
            if (
                record.to_date
                and record.from_date
                and record.to_date < record.from_date
            ):
                raise ValidationError("'To' date cannot be earlier than 'From' date.")
            if (
                record.to_date
                and record.from_date
                and self.diff_month(record.from_date, record.to_date) > 12
            ):
                raise ValidationError("Evaulation period cannot be exceed 1 year")

    # check overlap
    @api.onchange("from_date", "to_date")
    def _check_overlap(self):
        if self.from_date and self.to_date:
            evaulation_schedules = self.env["hr.evaluation.schedule"].search([])
            for evaulation_schedule in evaulation_schedules:
                if (
                    evaulation_schedule.from_date
                    < self.from_date
                    < evaulation_schedule.to_date
                ):
                    raise ValidationError(
                        f"Evaulation Schedule cannot be duplicated! exist in {evaulation_schedule.name}"
                    )
                if (
                    evaulation_schedule.from_date
                    < self.to_date
                    < evaulation_schedule.to_date
                ):
                    raise ValidationError(
                        f"Evaulation Schedule cannot be duplicated! exist in {evaulation_schedule.name}"
                    )
