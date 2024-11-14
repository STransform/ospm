from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from datetime import datetime

class HRStrategicPlan(models.Model):
    # Generate a list of years for selection fields, starting from the current year and extending 10 years forward
    @api.model
    def year_selection(self):
        year = datetime.now().year
        list_of_years = []

        for i in range(10):
            list_of_years.append((str(year),str(year)))
            year += 1

        return list_of_years 
        
    _name = "hr.strategic.plan"
    _description = "This is the strategic plan Model for the OSPM"

    # Fields related to the strategic plan
    department_id = fields.Many2one('hr.department', string= "Department")
    submitted_to = fields.Many2one("hr.department", string = "Submitted to")
    approved_by = fields.Many2one("res.users", string = "Approved by")
    is_approver = fields.Boolean(
        string="Is Approver", compute="_compute_is_approver", store=False
    )
   
    # Start and end year
    start_year = fields.Selection(
    year_selection,
    string="Start Year",
    )
    end_year = fields.Char(string="End Year")

    # Fields for total recruitment and promotion needs over the strategic period
    strategic_external_recruitment = fields.Integer(string="Total External Recruitment", required=True, default=0)
    strategic_promotion = fields.Integer(string="Total Promotion", required=True, default=0)
    strategic_total_need = fields.Integer(string="Strategic Total Need", required=True, default=0)

    # Status and description fields
    status = fields.Selection([
        ('draft', 'Draft'), 
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Current Stage", default='draft' )
    description = fields.Text(string="Description", required=True)
    comment = fields.Text(string="Comment")
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this training session.",
        required=True
    )

    # Override create method to perform validations on creation of a strategic plan
    @api.model
    def create(self, vals):
        # Get the current user's associated employee and department
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        dep_id  = vals['submitted_to']
        subbmited_to = self.env['hr.department'].search([('id', '=', dep_id)])
        # Ensure the selected department has a manager
        if not vals['attachment_ids'][0][-1]:
            raise ValidationError(_("The attachment file is required"))

        if not subbmited_to.manager_id:
            raise ValidationError(_("The selected department does not have a Manager. Please contact the administrator."))

        # Ensure the user is registered as an employee and a department manager
        if not employee:
            raise ValidationError(_("You are not registered as Employee. Please contact the administrator."))
        
        if not employee.department_id.manager_id:
            raise ValidationError(_("Your department doesn't have an assigned manager. Please contact the administrator."))

        if employee.department_id.manager_id != employee:
            raise ValidationError(_("You are not the Manager of this Department"))

        approved_user =subbmited_to.manager_id

        # Ensure the selected department has an approver and both years are specified
        if not approved_user.user_id:
            raise ValidationError(_("The selected department does not have an approver. Please contact the administrator."))

        if not vals['start_year'] or not vals['end_year']:
            raise ValidationError(_("Please enter the start year and end year."))

        # Check if the selected strategic plan period overlaps with any existing plans for the department
        depatrment_plans = self.env['hr.strategic.plan'].search([('department_id', '=', employee.department_id.id)]) 
        start_year = int(vals['start_year'])
        for plan in depatrment_plans:
            if int(plan.start_year) <= start_year <= int(plan.end_year) :
                raise ValidationError(_("The year you enter for the strategic plan is already covered by a previous plan. Please contact the administrator."))
        
        # check if the plan the approver is assigned to is all approved
        plans = self.env['hr.strategic.plan'].search([('approved_by', '=', self.env.uid),('start_year', '=', start_year)])
        if plans:
            for plan in plans:
                if plan.status != "approved":
                    raise ValidationError(_("All the Strategic plans for this period under you directory  must be approved first"))

        # Automatically set department ID, status, and approved_by fields if not provided in vals
        if 'department_id' not in vals:
            vals['department_id'] = employee.department_id.id
            vals['approved_by'] = approved_user.user_id.id
            vals['end_year'] = str(start_year + 4)
            vals['strategic_total_need'] = str(int(vals['strategic_external_recruitment'] + int(vals['strategic_promotion'])))
        return super(HRStrategicPlan, self).create(vals)

    # Compute whether the current user is the approver for this plan
    @api.depends("approved_by")
    def _compute_is_approver(self):
        for record in self:
            record.is_approver = record.approved_by.id == self.env.user.id
    
    # Onchange validation for ensuring a 5-year strategic period
    @api.onchange("start_year")
    def _onchange_year(self):
        if self.start_year:
            start_year = int(self.start_year)
            self.end_year = str(start_year + 4)
    
    # Compute total needs across years when values are changed for any year's recruitment or promotion
    @api.onchange("strategic_external_recruitment","strategic_promotion")
    def _onchange_(self):
        if self.strategic_external_recruitment < 0 or self.strategic_promotion < 0:
            raise ValidationError(_("Promotion and External Recruitment must be non-negative values."))
        self.strategic_total_need = self.strategic_external_recruitment + self.strategic_promotion
    # Action to submit the strategic plan
    def submit(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        manager = self.department_id.manager_id
        if not employee:
            raise ValidationError(_("You are not assigned to any department."))
    
        if employee.id != manager.id:
            raise ValidationError(_("You are not the Manager of this Department"))

        self.status = 'submitted'

    # Action to approve the strategic plan if the user is authorized
    def approve(self):
        if not self.is_approver:
            raise ValidationError(_("You are not authorized to approve this plan as it is outside your department hierarchy."))
        self.status = "approved"

    # Action to reject the strategic plan if the user is authorized and a comment is provided
    def reject(self):
        if not self.is_approver:
            raise ValidationError(_("You are not authorized to reject this plan as it is outside your department hierarchy."))
        if not self.comment:
            raise ValidationError(_("You need Comment to Reject the Plan"))
        self.status = "rejected"
