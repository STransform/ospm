from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError


class HrMedicalPreRequest(models.Model):
    _name = "hr.medical.pre.request"
    _description = "Medical Pre Request"
    _rec_name = "create_uid"
    _inherit = "mail.thread"
    _order = "create_date desc"

    description = fields.Text(string="Description", required=True, tracking=True)
    organization_id = fields.Many2one(
        "hr.medical.coverage.organization",
        string="Institution",
        required=True,
        tracking=True,
    )
    hr_comment = fields.Text(string="Hr Comment", tracking=True)
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("hr_rejected", "Hr Rejected"),
            ("hr_approved", "Hr Approved"),
        ],
        default="draft",
        string="Status",
        tracking=True,
    )
    is_employee = fields.Boolean(compute="_compute_is_employee", store=False)

    attachment_ids = fields.Many2many(
        "ir.attachment", string="Attachments", tracking=True
    )
    
    # validate for submition
    @api.depends('status')
    def _compute_is_employee(self):
        for record in self:
            record.is_employee = (
                record.create_uid.id == self.env.uid
                and record.status == "draft"
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
    def actionSubmit(self):
        self.status = "submitted"
        # send notification to hr
        hr_group = self.env.ref("user_group.group_hr_office")
        message = "New Medical Coverage Request"
        title = "New Medical Coverage Request"
        for user in hr_group.users:
            self.send_notification(
                message=message,
                user=user,
                title=title,
                model=self._name,
                res_id=self.id,
            )
            # web notify
            user.notify_success(title=title, message=message)
        self.env.user.notify_success("Request Submitted")

    def actionHrApprove(self):
        self.status = "hr_approved"
        # send notification to employee
        employee = self.create_uid
        message = "Medical Coverage Request Approved By HR"
        title = "Medical Coverage Request Approved By HR"
        self.send_notification(
            message=message,
            user=employee,
            title=title,
            model=self._name,
            res_id=self.id,
        )
        # web notify
        employee.notify_success(title=title, message=message)
        self.env.user.notify_success("Request Approved")
        
        

    def actionHrReject(self):
        self.status = "hr_rejected"
        # send notification to employee
        employee = self.create_uid
        message = "Medical Coverage Request Rejected By HR"
        title = "Medical Coverage Request Rejected By HR"
        self.send_notification(
            message=message,
            user=employee,
            title=title,
            model=self._name,
            res_id=self.id,
        )
        # web notify
        employee.notify_danger(title=title, message=message)
        self.env.user.notify_danger("Request Rejected")

    def write(self, vals):
        if "hr_comment" in vals:
            if not self.env.user.has_group("user_group.group_hr_office"):
                raise AccessError("You are not allowed to edit this field")
        return super(HrMedicalPreRequest, self).write(vals)
