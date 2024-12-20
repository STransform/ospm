# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_attendance_use_pin = fields.Boolean(
        string='Employee PIN',
        implied_group="hr_attendance.group_hr_attendance_use_pin")
    hr_attendance_overtime = fields.Boolean(
        string="Count Extra Hours", readonly=False)
    overtime_start_date = fields.Date(string="Extra Hours Starting Date", readonly=False)
    overtime_company_threshold = fields.Integer(
        string="Tolerance Time In Favor Of Company", readonly=False)
    overtime_employee_threshold = fields.Integer(
        string="Tolerance Time In Favor Of Employee", readonly=False)
    attendance_kiosk_mode = fields.Selection(related='company_id.attendance_kiosk_mode', readonly=False)
    attendance_barcode_source = fields.Selection(related='company_id.attendance_barcode_source', readonly=False)
    attendance_kiosk_delay = fields.Integer(related='company_id.attendance_kiosk_delay', readonly=False)
    late_in_time = fields.Char(
        string="Late In Time Limit",
        default="08:30",
        help="Late In starts after this time (e.g., '08:30' for 8:30 AM)"
    )
    early_out_time = fields.Char(
        string="Early Out Time Limit",
        default="17:00",
        help="Early Out is before this time (e.g., '17:00' for 5:00 PM)"
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update({
            'late_in_time': self.env['ir.config_parameter'].sudo().get_param('hr_attendance.late_in_time', default="08:30"),
            'early_out_time': self.env['ir.config_parameter'].sudo().get_param('hr_attendance.early_out_time', default="17:00"),
        })
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('hr_attendance.late_in_time', self.late_in_time)
        self.env['ir.config_parameter'].sudo().set_param('hr_attendance.early_out_time', self.early_out_time)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        company = self.env.company
        res.update({
            'hr_attendance_overtime': company.hr_attendance_overtime,
            'overtime_start_date': company.overtime_start_date,
            'overtime_company_threshold': company.overtime_company_threshold,
            'overtime_employee_threshold': company.overtime_employee_threshold,
        })
        return res

    def set_values(self):
        super().set_values()
        company = self.env.company
        # Done this way to have all the values written at the same time,
        # to avoid recomputing the overtimes several times with
        # invalid company configurations
        fields_to_check = [
            'hr_attendance_overtime',
            'overtime_start_date',
            'overtime_company_threshold',
            'overtime_employee_threshold',
        ]
        if any(self[field] != company[field] for field in fields_to_check):
            company.write({field: self[field] for field in fields_to_check})
