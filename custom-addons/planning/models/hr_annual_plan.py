from odoo import api,fields, _, models
from odoo.exceptions import ValidationError,UserError
from datetime import datetime

class HrAnnualPlan(models.Model):
    # Generate a list of years for selection fields, starting from the current year and extending 10 years forward
    @api.model
    def year_selection(self):
        year = datetime.now().year
        list_of_years = []

        for i in range(10):
            list_of_years.append((str(year),str(year)))
            year += 1

        return list_of_years 

    _name = "hr.annual.plan"
    _description = "HR Annual Plan"

    department_id = fields.Many2one("hr.department", string="Department")
    submitted_to = fields.Many2one("hr.department", string="Submitted to")
    approved_by = fields.Many2one("res.users", string = "Approved by")
    
    is_approver = fields.Boolean(
        string="Is Approver", compute="_compute_is_approver", store=False
    )
    year = fields.Selection(year_selection,string="Year", required=True)
    external_recruitment = fields.Integer(string="External Recruitment", required=True)
    promotion = fields.Integer(string="Promotion", required=True)
    total_need = fields.Integer(string="Total Need")
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
        help="Attach documents related to this training session."
    )
    

    @api.depends("approved_by")
    def _compute_is_approver(self):
        for record in self:
            record.is_approver = record.approved_by.id == self.env.user.id

    @api.model
    def create(self, vals):
        year = vals['year']
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        dep_id  = vals['submitted_to']
        subbmited_to = self.env['hr.department'].search([('id', '=', dep_id)])

        if not vals['attachment_ids'][0][-1]:
            raise ValidationError(_("The attachment file is required"))

        if not subbmited_to.manager_id:
            raise ValidationError(_("The selected department does not have a Manager. Please contact the administrator."))
 
        if not employee:
            raise ValidationError(_("You are not registered as Employee. Please contact the administrator."))

        if not employee.department_id.manager_id:
            raise ValidationError(_("Your department doesn't have an assigned manager. Please contact the administrator."))

        if employee.department_id.manager_id != employee:
            raise ValidationError(_("You are not the Manager of this Department"))

        approved_user =subbmited_to.manager_id

        if not approved_user.user_id:
            raise ValidationError(_("The selected department does not have an approver. Please contact the administrator."))

        if not vals['year']:
            raise ValidationError(_("Please enter the year."))

        depatrment_plans = self.env['hr.annual.plan'].search([('department_id', '=', employee.department_id.id)]) 
        year = vals['year']
        for plan in depatrment_plans:
            if plan.year == vals['year']:
                raise ValidationError(_("The year you enter for the annual plan is already covered by a previous plan. Please contact the administrator."))
        
        plans = self.env['hr.annual.plan'].search([('approved_by', '=', self.env.uid),('year', '=', year)])
        for plan in plans:
            if plan.status != "approved":
                raise ValidationError(_(f"All the annual plans for {year} under you directory  must be approved first"))
        ## add validaton for the hr Annual plan depending on the Strategic HR Plan

        strategic_plans = self.env['hr.strategic.plan'].search([('department_id', '=', employee.department_id.id)])
        plan_found = False
        strategic_external_recruitment = 0
        strategic_promotion = 0
        strategic_start_year = 0
        strategic_end_year = 0
        for plan in strategic_plans:
            if int(plan.start_year) <= int(year) <= int(plan.end_year):
                plan_found = True
                strategic_external_recruitment = plan.strategic_external_recruitment
                strategic_promotion = plan.strategic_promotion
                strategic_start_year = int(plan.start_year)
                strategic_end_year = int(plan.end_year)
                if plan.status != "approved":
                    raise ValidationError(_(f"The Strategic plan that include {year} must be approved first"))
        if not plan_found:
            raise ValidationError(_(f"There is no Strategic plan for {year}"))

        annual_plans = self.env['hr.annual.plan'].search([('department_id', '=', employee.department_id.id)])
        for plan in annual_plans:
            if strategic_start_year <= int(plan.year) <= strategic_end_year:
                strategic_promotion -= plan.promotion
                strategic_external_recruitment -= plan.external_recruitment
                
        if strategic_promotion < vals['promotion'] or strategic_external_recruitment < vals['external_recruitment']:
            raise ValidationError(_(f"The Strategic plan that include {year} must be approved first")) 
            
        if 'department_id' not in vals:
            vals['department_id'] = employee.department_id.id
            vals['approved_by'] = approved_user.user_id.id
            vals['total_need'] = vals['promotion'] + vals['external_recruitment']
        return super(HrAnnualPlan, self).create(vals)

    @api.onchange('promotion','external_recruitment')
    def _onchange_(self):
        if self.promotion < 0 or self.external_recruitment < 0:
            raise UserError("Promotion and External Recruitment must be non-negative values.")
        self.total_need = self.promotion + self.external_recruitment

    def submit(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        manager = self.department_id.manager_id
        if not employee:
            raise ValidationError(_("You are not assigned to any department."))
    
        if employee.id != manager.id:
            raise ValidationError(_("You are not the Manager of this Department"))

        self.status = 'submitted'

    def approve(self):
        if not self.is_approver:
            raise ValidationError(_("You are not authorized to approve this plan as it is outside your department hierarchy."))
        self.status = "approved"

    def reject(self):
        if not self.is_approver:
            raise ValidationError(_("You are not authorized to reject this plan as it is outside your department hierarchy."))
        if not self.comment:
            raise ValidationError(_("You need Comment to Reject the Plan"))
        self.status = "rejected"

