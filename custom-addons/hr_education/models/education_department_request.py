from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class EducationDepartmentRequest(models.Model):
    _name = 'education.department.request'
    _description = 'Education Department Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def year_selection(self):
        year = datetime.now().year
        list_of_years = []

        for i in range(10):
            list_of_years.append((str(year),str(year)))
            year += 1

        return list_of_years 

    name = fields.Char(string="Request Name", compute="_compute_name", store=True)
    education_programs = fields.One2many('education.program', 'education_id', string='Education Programs')
    description = fields.Text(string='Description')
    department_id = fields.Many2one('hr.department', string='Department', required=True, readonly=True, default=lambda self: self._get_default_department())
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this education program.",
        required=True,
    )
    year = fields.Selection(year_selection,string="Year", required=True)
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),('requested', 'Approval Requested'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='draft',
        store=True,
    )


    total_employee_count = fields.Integer(
        string="Total Employees",
        compute="_compute_total_employee_count",
        store=True,
        help="Total number of employees across all education programs."
    )

    @api.depends('year','department_id')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.department_id.name} Education Plan for {record.year}" if record.year else f"{record.department_id.name} Education Plan for -"

    @api.depends('education_programs.employee_count')
    def _compute_total_employee_count(self):
        for record in self:
            record.total_employee_count = sum(program.employee_count for program in record.education_programs)


    @api.model
    def _get_default_department(self):
        """Fetch the department of the currently logged-in user."""
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if not employee or not employee.department_id:
            raise UserError("No department is assigned to the current user.")
        return employee.department_id.id
    
    def action_request_approval(self):
        for record in self:
            if record.department_id.manager_id.user_id.id != self.env.uid:
                raise ValidationError("You are not authorized to request approval for this department.")
            record.state = 'requested'

    def action_approve_request(self):
        for record in self:
            record.state = 'approved'

    def action_reject_request(self):
        for record in self:
            record.state = 'rejected'
    

    _sql_constraints = [
        (
            'unique_year_per_department',
            'UNIQUE(year, department_id)',
            'The Year must be unique for each department!'
        ),
    ]