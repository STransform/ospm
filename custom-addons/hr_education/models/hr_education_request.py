from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class HrEducationRequest(models.Model):
    _name = 'hr.education.request'
    _description = 'HR Education Request'
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
    education_programs = fields.One2many('hr.education.program', 'education_id', string='Education Programs')
    description = fields.Text(string='Description')
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attach documents related to this education program.",
    )

    year = fields.Selection(year_selection, string="Year", required=True)
    state_by_ceo = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ])

    state_by_planning = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ])

    combined_state = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('pending', 'Pending'),
    ], string="Combined State", compute='_compute_combined_state', store=True)
 


    state = fields.Selection(
        string='State',
        selection=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending',
        store=True,
    )

    total_employee_count = fields.Integer(
        string="Total Employees",
        compute="_compute_total_employee_count",
        store=True,
        help="Total number of employees across all education programs."
    )
    
    @api.depends('education_programs.employee_count')
    def _compute_total_employee_count(self):
        for record in self:
            record.total_employee_count = sum(program.employee_count for program in record.education_programs)

    @api.depends('year')
    def _compute_name(self):
        for record in self:
            record.name = f"HR Office Education Plan for {record.year}" if record.year else "HR Office Education Plan for -"
    
    @api.depends('state_by_ceo', 'state_by_planning')
    def _compute_combined_state(self):
        for record in self:
            if 'rejected' in [record.state_by_planning, record.state_by_ceo]:
                record.combined_state = 'rejected'
            elif all(state == 'approved' for state in [record.state_by_planning, record.state_by_ceo]):
                record.combined_state = 'approved'
            else:
                record.combined_state = 'pending'


    def action_approve_ceo(self):
        for record in self:
            record.state_by_ceo = 'approved'

    def action_reject_ceo(self):
        for record in self:
            record.state_by_ceo = 'rejected'

    def action_approve_planning(self):
        for record in self:
            record.state_by_planning = 'approved'

    def action_reject_planning(self):
        for record in self:
            record.state_by_planning = 'rejected'
            
    def action_resubmit_planning(self):
        for record in self:
            record.state_by_planning = 'pending'

    _sql_constraints = [
        (
            'unique_year',
            'UNIQUE(year)',
            'The Year must be unique'
        ),
    ]