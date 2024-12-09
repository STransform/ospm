from odoo import models, fields, api, SUPERUSER_ID,_
from datetime import date
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    near_retirement = fields.Boolean(string="Near Retirement", compute="_compute_near_retirement", store=True )
    is_retired = fields.Boolean(string="Is Retired", default=False, readonly=True)
    has_birthday = fields.Boolean(string="Has Birthday", compute="_compute_near_retirement", store=True)
    retirement_date = fields.Date(string="Retirement Date", compute="_compute_near_retirement", store=True)
    retirement_extended = fields.Boolean(string="Retirement Extended", default=False, store=True)
    department = fields.Char(string="Department", related='department_id.name', readonly=True)

    @api.depends('birthday')
    def _compute_near_retirement(self):
        """Compute whether an employee is near retirement based on age."""
        retirement_age_limit = self.env['hr.retirement.settings'].sudo().search([], limit=1).retirement_age
        retirement_threshold = self.env['hr.retirement.settings'].sudo().search([], limit=1).retirement_threshold_months
        for employee in self:
            if employee.is_retired:
                employee.near_retirement = False
                employee.retirement_date = None
                continue
            if employee.retirement_extended:
                if date.today() >= employee.retirement_date - relativedelta(months=retirement_threshold):
                    employee.near_retirement = True
                else:
                    employee.near_retirement = False
                
            elif employee.birthday:
                current_age = relativedelta(date.today(), employee.birthday).years
                employee.retirement_date = employee.birthday + relativedelta(years=retirement_age_limit)
                if current_age >= (retirement_age_limit - int(retirement_threshold) / 12):
                    employee.near_retirement = True
                else:
                    employee.near_retirement = False
                employee.has_birthday = True

            else:
                employee.has_birthday = False
                employee.near_retirement = False
                employee.retirement_date = None

    def update_near_retirement(self):
        """Update the near retirement status for all employees."""
        employees = self.search([])
        employees._compute_near_retirement()  # Re-compute the near retirement status for all employees

    @api.onchange('birthday')
    def _onchange_birthday(self):
        if self.birthday and self.birthday >= date.today():
            raise ValidationError(_("Birthday cannot be in the future."))
        """Update the retirement date when the birthday is changed."""
        retirement_age_limit = self.env['hr.retirement.settings'].sudo().search([], limit=1).retirement_age
        if self.birthday:
            self.retirement_date = self.birthday + relativedelta(years=retirement_age_limit)
        else:
            self.retirement_date = None


def update_near_retirement_post_install(cr, registry):
    """Update the near retirement status for all employees after the module is installed."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    employees =  env['hr.employee'].search([])
    employees._compute_near_retirement() 