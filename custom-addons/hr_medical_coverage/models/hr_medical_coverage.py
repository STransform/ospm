# hr_medical_coverage.py

from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError


class HrMedicalCoverage(models.Model):
    _name = "hr.medical.coverage"
    _description = "Medical Coverage Request"
    _inherit = ["mail.thread"]
    _rec_name = "create_uid"
    _order = "create_date desc"

    description = fields.Text(string="Description", required=True, tracking=True)
    hr_comment = fields.Text(string="Hr Director Comment", tracking=True)
    finance_comment = fields.Text(string="Finance Comment", tracking=True)
    totalRequestedAmount = fields.Float(
        string="Total Requested Amount",
        compute="_compute_total_amount",
        store=True,
        tracking=True,
    )
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("hr_approved", "HR Approved"),
            ("hr_rejected", "HR Rejected"),
            ("finance_approved", "Finance Approved"),
            ("finance_rejected", "Finance Rejected"),
        ],
        default="draft",
        string="Status",
        tracking=True,
    )
    is_employee = fields.Boolean(compute="_compute_is_employee", store=False)

    # Medical Cost List
    costItemIds = fields.One2many(
        "hr.medical.cost.item",
        "coverageId",
        string="Medical Cost Items",
        required=True,
        tracking=True,
    )

    # Attachments
    attachment_ids = fields.Many2many(
        "ir.attachment", string="Attachments", tracking=True
    )

    # validation for submitio
    @api.depends("status")
    def _compute_is_employee(self):
        for record in self:
            record.is_employee = (
                record.create_uid.id == self.env.uid and record.status == "draft"
            )

    @api.depends("costItemIds.amount")
    def _compute_total_amount(self):
        for record in self:
            record.totalRequestedAmount = sum(
                item.amount for item in record.costItemIds
            )

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


    # Methods for request submission and approvals
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
        # send notification to finance
        finance_group = self.env.ref("user_group.group_finance_office")
        message = "Medical Coverage Request Approved"
        title = "Medical Coverage Request Approved"
        for user in finance_group.users:
            self.send_notification(
                message=message,
                user=user,
                title=title,
                model=self._name,
                res_id=self.id,
            )
            # web notify
            user.notify_success(title=title, message=message)
        self.env.user.notify_success("Request Approved")
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
        self.env.user.notify_danger("Successfully Rejected")
        

    def actionFinanceApprove(self):
        self.status = "finance_approved"
        # send notification to employee
        employee = self.create_uid
        message = "Medical Coverage Request Approved By Finance"
        title = "Medical Coverage Request Approved By Finance"
        self.send_notification(
            message=message,
            user=employee,
            title=title,
            model=self._name,
            res_id=self.id,
        )
        # web notify
        self.env.user.notify_success("Successfully Approved")
        employee.notify_success(title=title, message=message)
        

    def actionFinanceReject(self):
        self.status = "finance_rejected"
        self.env.user.notify_danger("Successfully Rejected")
        # send notification to employee
        employee = self.create_uid
        message = "Medical Coverage Request Rejected By Finance"
        title = "Medical Coverage Request Rejected By Finance"
        self.send_notification(
            message=message,
            user=employee,
            title=title,
            model=self._name,
            res_id=self.id,
        )
        employee.notify_danger(title=title, message=message)
        

    # Amount Validation
    @api.constrains("totalRequestedAmount")
    def _check_total_requested_amount(self):
        for record in self:
            if record.totalRequestedAmount < 1:
                raise ValidationError(
                    "Invalid Input: The Total Requested Amount should be a positive number."
                )

    @api.onchange("totalRequestedAmount")
    def _onchange_total_requested_amount(self):
        if self.totalRequestedAmount < 0:
            return {
                "warning": {
                    "title": "Invalid Input",
                    "message": "Amount should be a positive number.",
                }
            }

    def write(self, vals):
        # Check if hr_comment is being modified
        if "hr_comment" in vals:
            # Check if the current user is in the HR Director group
            if not self.env.user.has_group("user_group.group_hr_office"):
                raise AccessError("You are not allowed to edit the HR Comment field.")

        # check if finance comment is changed
        if "finance_comment" in vals:
            if not self.env.user.has_group("user_group.group_finance_office"):
                raise AccessError(
                    "You are not allowed to edit the Finance Comment field."
                )

        return super(HrMedicalCoverage, self).write(vals)

    # Hr description read only

    # # notification
    # def actionSubmit(self):
    #     self.status = 'submitted'

    #     # Get HR and Finance Officers' user IDs
    #     hr_group = self.env.ref('user_group.group_hr_office')
    #     finance_group = self.env.ref('user_group.group_finance_office')
    #     user_ids = hr_group.users.ids + finance_group.users.ids

    #     # Send real-time notifications
    #     for user_id in user_ids:
    #         self.env['bus.bus'].sendone(
    #             (self._cr.dbname, 'res.partner', user_id),  # Channel
    #             {
    #                 'type': 'simple_notification',
    #                 'title': ("New Medical Coverage Request"),
    #                 'message': ("A new medical coverage request has been submitted."),
    #                 'sticky': False,  # Set to True if you want the popup to remain visible until manually closed
    #             }
    #         )
