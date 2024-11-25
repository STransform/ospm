from odoo import api, fields, models
from odoo.exceptions import UserError


class EmployeePromotion(models.Model):
    """This model is necessary for add employee promotion details in employee
       module """
    _name = 'employee.promotion'
    _description = 'Employee Promotion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'promotion_name'

    promotion_name = fields.Text(required=True, string='Promotion Name',
                                 help='Promotion name')
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  help='Name of employee')
    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  help='Contract of employee',
                                  domain="[('employee_id', '=', employee_id)]")
    job_title_id = fields.Many2one('hr.job', string='Old Position',
                                   help='Previous job of employee ')
    
    promotion_date = fields.Date(string='Promotion Date',
                                 default=fields.Date.today(),
                                 help='Date of promotion date')
    
    promotion_type_id = fields.Many2one('promotion.type',
                                        string='Promotion Type',
                                        help='Promotion type of promotion')
    new_designation_id = fields.Many2one('hr.job', string='New Position',
                                         help='New designation of employee')
   
    description = fields.Text(string='Description', help='Description')


    @api.model
    def create(self, vals):
        """It checks if the new salary is greater than the old salary,
           raising a UserError if it is not the case."""
        res = super(EmployeePromotion, self).create(vals)
        employee = self.env['hr.employee'].browse(res.employee_id.id)
        employee.write({
            'promotion_ids': [(4, res.id)],
            'job_id': res.new_designation_id.id
        })
        return res


    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.job_title_id = self.employee_id.job_id.id
        contract = self.env['hr.contract.history'].search(
            [('employee_id', '=', self.employee_id.id),
             ('state', '=', 'open')])
        if contract:
            for contract_history in contract:
                self.contract_id = contract_history.name
            



