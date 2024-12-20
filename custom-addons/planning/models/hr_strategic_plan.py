from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from datetime import datetime

class HRStrategicPlan(models.Model):
    # Generate a list of years for selection fields, starting from the current year and extending 10 years forward
    @api.model 
    def year_selection(self):
        year = datetime.now().year
        return [(str(y), str(y)) for y in range(year, year + 10)]
    _name = "hr.strategic.plan"
    _description = "Strategic Plan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'department_id'

    department_id = fields.Many2one('hr.department', string="Department", required=True, readonly=True, default=lambda self: self._default_department_id())
    submitted_to = fields.Many2one("hr.department", string="Submitted to", required=True)
    approved_by = fields.Many2one("res.users", string="Approved by", compute='_compute_submitted_to', store=False)
    start_year = fields.Selection(year_selection, string="Start Year", required=True)
    end_year = fields.Char(string="End Year", compute='_compute_end_year', store=True)
    strategic_external_recruitment = fields.Integer(string="Total External Recruitment", required=True, default=0)
    strategic_promotion = fields.Integer(string="Total Promotion", required=True, default=0) 
    strategic_total_need = fields.Integer(string="Strategic Total Need", compute='_compute_total_need', store=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'), 
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Current Stage", default='draft')
    description = fields.Text(string="Description", required=True)
    comment = fields.Text(string="Comment")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', required=True,
        help="Attach documents related to this training session.")

    is_approver = fields.Boolean(string="Is Approver", compute="_compute_is_approver", store=False )



    @api.model
    def send_notification(self, message, user, title,model,res_id):
        """
        Send a notification to a specific user.
        
        Args:
            message (str): The notification message
            user (res.users): The user to notify
            title (str): The notification title
            model (str): The model name
            res_id (int): The record ID
        """
        self.env['custom.notification'].create({
            'title': title,
            'message': message,
            'user_id': user.id,
            'action_model':model,
            'action_res_id': res_id
        })

    @api.model
    def _default_department_id(self):
        employee = self.env.user.employee_id
        if not employee:
            raise ValidationError(_("You are not registered as an employee. Please contact the administrator."))
        if not employee.department_id:
            raise ValidationError(_("You are not assigned to any department. Please contact the administrator."))
        if not employee.department_id.manager_id:
            raise ValidationError(_("Your department does not have a manager assigned. Please contact the administrator."))
        if employee.id != employee.department_id.manager_id.id:
            raise ValidationError(_("You are not the manager of your department. Please contact the administrator."))
        return employee.department_id.id


    @api.depends('submitted_to')
    def _compute_submitted_to(self):
        # Cannot submit to own department
        if self.submitted_to and self.submitted_to.id == self.department_id.id:
            raise ValidationError(_("You cannot submit the plan to your own department."))
        if self.submitted_to and not self.submitted_to.manager_id:
            raise ValidationError(_("The selected department does not have a manager assigned."))
        if self.submitted_to and not self.submitted_to.manager_id.user_id:
            raise ValidationError(_("The selected department does not have a manager assigned. user"))
        
        self.approved_by = self.submitted_to.manager_id.user_id.id
    

    @api.depends('start_year')
    def _compute_end_year(self):
        if self.start_year:
            self.end_year = str(int(self.start_year) + 4)
            

    @api.depends('strategic_external_recruitment', 'strategic_promotion')
    def _compute_total_need(self):
        self.strategic_total_need = self.strategic_external_recruitment + self.strategic_promotion


    @api.model
    def _compute_is_approver(self):
        self.is_approver = self.approved_by.id == self.env.user.id
    
    @api.onchange('start_year')
    def _onchange_start_year(self):
        if self.start_year:
            plans = self.env['hr.strategic.plan'].search([
                ('department_id', '=', self.department_id.id)
            ])
            for plan in plans:
                if int(plan.start_year) <= int(self.start_year) <= int(plan.end_year):
                    raise ValidationError(_("The year you enter for the strategic plan is already covered by a previous plan."))


    @api.onchange("strategic_external_recruitment","strategic_promotion")
    def _onchange_(self):
        if self.strategic_external_recruitment < 0 or self.strategic_promotion < 0:
            raise ValidationError(_("Promotion and External Recruitment must be non-negative values."))
        self.strategic_total_need = self.strategic_external_recruitment + self.strategic_promotion

    
    def action_submit(self):
        if self.status != 'draft':
            raise ValidationError(_("You can not submit this plan as it is not in draft stage."))
        self.status = "submitted"
        message = f"{self.department_id.manager_id.name} has Submitted the Strategic plan for {self.department_id.name} from {self.start_year} - {self.end_year}"
        self.send_notification(message=message, user=self.approved_by, title=self._description, model=self._name, res_id=self.id)
        self.approved_by.notify_info(message=message, title=self._description)
        self.env.user.notify_success(message="Plan Submitted Successfully", title=self._description)

    def action_approve(self):
        if not self.is_approver:
            raise ValidationError(_("You are not authorized to approve this plan as it is outside your department hierarchy."))
        if self.status != 'submitted':
            raise ValidationError(_("You can not approve this plan as it is not in submitted stage."))
        self.status = "approved"
        message = f"The {self.approved_by.name} has Approved the Strategic plan for {self.start_year} - {self.end_year}"
        self.send_notification(message=message, user=self.create_uid, title=self._description, model=self._name, res_id=self.id)
        self.create_uid.notify_success(message="Plan Approved Successfully", title=self._description)
        self.env.user.notify_success(message="Plan Approved Successfully", title=self._description)

    def action_reject(self):
        if not self.is_approver:
            raise ValidationError(_("You are not authorized to reject this plan as it is outside your department hierarchy."))
        if not self.comment:
            raise ValidationError(_("You need Comment to Reject the Plan"))
        if self.status != 'submitted':
            raise ValidationError(_("You can not reject this plan as it is not in submitted stage."))
        self.status = "rejected"
        message = f"The {self.approved_by.name} has Rejected the Strategic plan for {self.start_year} - {self.end_year}"
        self.send_notification(message=message, user=self.create_uid, title=self._description, model=self._name, res_id=self.id)
        self.create_uid.notify_warning(message="Plan Rejected Successfully", title=self._description)
        self.env.user.notify_warning(message="Plan Rejected Successfully", title=self._description)
    
    def action_resubmit(self):
        if self.status != 'rejected':
            raise ValidationError(_("You can not resubmit this plan as it is not in rejected stage."))
        if self.env.user.id != self.department_id.manager_id.user_id.id:
            raise ValidationError(_("You can not resubmit this plan as you are not the Department Manager."))
        self.status = "submitted"
        message = f"{self.department_id.manager_id.name} has Resubmitted the Strategic plan for {self.department_id.name} from {self.start_year} - {self.end_year}"
        self.send_notification(message=message, user=self.approved_by, title=self._description, model=self._name, res_id=self.id)
        self.approved_by.notify_info(message=message, title=self._description)
        self.env.user.notify_success(message="Plan Resubmitted Successfully", title=self._description)
