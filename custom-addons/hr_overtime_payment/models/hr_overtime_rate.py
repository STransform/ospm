from odoo import api, models, fields


class HrOvertimeType(models.Model):
    _name = "hr.overtime.rate"
    _description = "Overtime Rate Types"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

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
    hourly_rate = fields.Float(string="Hourly Rate (%)", required=True, tracking=True)

    _sql_constraints = [
        ("unique_rate_type", "UNIQUE(name)", "The overtime rate type must be unique.")
    ]
