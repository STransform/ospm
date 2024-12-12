from odoo import api, models, fields
from odoo.exceptions import ValidationError


class HrOvertimeType(models.Model):
    _name = "hr.overtime.rate"
    _description = "Overtime Rate Types"
    _inherit = ["mail.thread"]
    _order = "create_date desc"
    _rec_name = "display_name"

    name = fields.Selection(
        [
            ("normal_day", "Regular Day (6 a.m. to 10 p.m.)"),
            ("night_shift", "Night Shift (10 p.m. to 6 a.m.)"),
            ("weekly_rest", "Weekly Rest Day"),
            ("public_holiday", "Public Holiday"),
        ],
        string="Overtime Rate Type",
        required=True,
    )
    display_name = fields.Char(string="Display Name", compute="_compute_display_name")
    hourly_rate = fields.Float(string="Hourly Rate (%)", required=True, tracking=True)

    _sql_constraints = [
        ("unique_rate_type", "UNIQUE(name)", "The overtime rate type must be unique.")
    ]
    
    @api.constrains("hourly_rate")
    def _check_hourly_rate(self):
        for record in self:
            if record.hourly_rate <= 0:
                raise ValidationError("The Hourly Rate should be positive number!")
    
    @api.constrains('name')
    def _check_name_unique(self):
        for record in self:
            if self.search_count([('name', '=', record.name)]) > 1:
                raise ValidationError(f"The rate type '{record.name}' already exists. Please provide a unique name.")

    @api.depends('name')
    def _compute_display_name(self):
        selection_dict = dict(self._fields['name'].selection)
        for record in self:
            record.display_name = selection_dict.get(record.name, '')