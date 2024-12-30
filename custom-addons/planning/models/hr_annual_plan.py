from odoo import api,fields, _, models
from odoo.exceptions import ValidationError,UserError
from datetime import datetime

class HrAnnualPlan(models.Model):
    # Generate a list of years for selection fields, starting from the current year and extending 10 years forward
    @api.model 
    def year_selection(self):
        year = datetime.now().year
        return [(str(y), str(y)) for y in range(year, year + 10)]

    _name = "hr.annual.plan"
    _description = "HR Annual Plan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'department_id'

    department_id = fields.Many2one('hr.department', string="Department", required=True, readonly=True, default=lambda self: self._default_department_id())
    submitted_to = fields.Many2one("hr.department", string="Submitted to")
    approved_by = fields.Many2one("res.users", string="Approved by", compute='_compute_submitted_to',search="_search_approved_by", store=False)
    year = fields.Selection(year_selection,string="Year", required=True)
    external_recruitment = fields.Integer(string="External Recruitment", required=True)
    promotion = fields.Integer(string="Promotion", required=True)
    total_need = fields.Integer(string="Strategic Total Need", compute='_compute_total_need', store=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Current Stage", default='draft' )
    description = fields.Text(string="Description", required=True)
    comment = fields.Text(string="Comment")
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments', required=True,
        help="Attach documents related to this training session."
    )

    is_approver = fields.Boolean(string="Is Approver", compute="_compute_is_approver", store=False )

    _sql_constraints = [
        ('unique_year_department', 'unique (year, department_id)', 'Year and Department must be unique.')
    ]


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
    

    def _search_approved_by(self, operator, value):
        """
        Custom search function for is_department_manager field.
        
        Args:
            operator (str): Search operator ('=' or '!=')
            value (bool): Search value
            
        Returns:
            list: Domain for search
            
        Raises:
            ValueError: If operator not supported
        """
        if operator not in ['=', '!=']:
            raise ValueError("Operator not supported for this field.")
        
        user_id = self.env.uid
        # Query departments where the logged-in user is the manager
        department_ids = self.env['hr.department'].search([('manager_id.user_id', '=', user_id)]).ids

        # Match records with the queried departments
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('department_id', 'in', department_ids)]
        else:
            return [('department_id', 'not in', department_ids)]

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
    

    @api.depends("approved_by")
    def _compute_is_approver(self):
        for record in self:
            record.is_approver = record.approved_by.id == self.env.user.id


    @api.onchange('promotion','external_recruitment')
    def _onchange_(self):
        if self.promotion < 0 or self.external_recruitment < 0:
            raise UserError("Promotion and External Recruitment must be non-negative values.")
        self.total_need = self.promotion + self.external_recruitment

    @api.depends('external_recruitment', 'promotion')
    def _compute_total_need(self):
        self.total_need = self.promotion + self.external_recruitment

    def _get_strategic_year(self,year):
        strategic_plans = self.env['hr.strategic.plan'].search([
                ('department_id', '=', self.department_id.id),
            ])
        for plan in strategic_plans:
            if int(plan.start_year) <= year <= int(plan.end_year) and plan.status == 'approved':
                return  plan
        return None

    @api.onchange('year', 'promotion','external_recruitment')
    def _check_annual_plan_against_strategic_plan(self):
        if self.year:
            strategic_plan = self._get_strategic_year(int(self.year))
            if not strategic_plan:
                raise ValidationError(_(
                    "No strategic plan covers the year %s for the department %s. Please ensure a strategic plan exists." % (self.year, self.department_id.name)
                ))
            
            strategic_plan_start_year = int(strategic_plan.start_year)
            strategic_plan_end_year = int(strategic_plan.end_year)
            strategic_plan_total_need = strategic_plan.strategic_total_need
            strategic_plan_promotion = strategic_plan.strategic_promotion
            strategic_plan_external_recruitment = strategic_plan.strategic_external_recruitment

            annual_plans = self.env['hr.annual.plan'].search([
                ('department_id', '=', self.department_id.id),
            ])
            print("================> anual plan",)
            for plan in annual_plans:
                if strategic_plan_start_year <= int(plan.year) <= strategic_plan_end_year and  plan.status == 'approved':
                    if plan.year == self.year:
                        raise ValidationError(_(
                            "An approved annual plan for the year %s already exists. Please ensure the annual plan is unique." % (self.year)
                        ))
                    strategic_plan_total_need -= plan.total_need
                    strategic_plan_promotion -= plan.promotion
                    strategic_plan_external_recruitment -= plan.external_recruitment

            if strategic_plan_total_need < self.total_need:
                raise ValidationError(_(
                    "The annual plan for the year %s exceeds the strategic plan total need. Please ensure the annual plan is within the strategic plan limits." % (self.year)
                ))
            
            if strategic_plan_promotion < self.promotion:
                raise ValidationError(_(
                    "The annual plan for the year %s exceeds the strategic plan promotion. Please ensure the annual plan is within the strategic plan limits." % (self.year)
                ))
            
            if strategic_plan_external_recruitment < self.external_recruitment:
                raise ValidationError(_(
                    "The annual plan for the year %s exceeds the strategic plan external recruitment. Please ensure the annual plan is within the strategic plan limits." % (self.year)
                ))
    
    def action_submit(self):
        if self.status != 'draft':
            raise ValidationError(_("You can not submit this plan as it is not in draft stage."))
        self.status = "submitted"
        message = f"{self.department_id.manager_id.name} has Submitted {self.year} Annual plan for {self.department_id.name}"
        self.send_notification(message=message, user=self.approved_by, title=self._description, model=self._name, res_id=self.id)
        self.approved_by.notify_info(message=message, title=self._description)
        self.env.user.notify_success(message="Plan Submitted Successfully", title=self._description)

    def action_approve(self):
        if not self.is_approver:
            raise ValidationError(_("You are not authorized to approve this plan as it is outside your department hierarchy."))
        if self.status != 'submitted':
            raise ValidationError(_("You can not approve this plan as it is not in submitted stage."))
        self.status = "approved"
        message = f"The {self.approved_by.name} has Approved the Annual plan for {self.year}"
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
        message = f"The {self.approved_by.name} has Rejected the Annual plan for {self.year}"
        self.send_notification(message=message, user=self.create_uid, title=self._description, model=self._name, res_id=self.id)
        self.create_uid.notify_warning(message="Plan Rejected Successfully", title=self._description)
        self.env.user.notify_warning(message="Plan Rejected Successfully", title=self._description)
    
    def action_resubmit(self):
        if self.status != 'rejected':
            raise ValidationError(_("You can not resubmit this plan as it is not in rejected stage."))
        if self.env.user.id != self.department_id.manager_id.user_id.id:
            raise ValidationError(_("You can not resubmit this plan as you are not the Department Manager."))
        self.status = "submitted"
        message = f"{self.department_id.manager_id.name} has Resubmitted {self.year} Annual plan for {self.department_id.name}"
        self.send_notification(message=message, user=self.approved_by, title=self._description, model=self._name, res_id=self.id)
        self.approved_by.notify_info(message=message, title=self._description)
        self.env.user.notify_success(message="Plan Resubmitted Successfully", title=self._description)

