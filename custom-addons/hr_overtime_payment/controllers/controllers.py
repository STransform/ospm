# -*- coding: utf-8 -*-
# from odoo import http


# class HrOvertimePayment(http.Controller):
#     @http.route('/hr_overtime_payment/hr_overtime_payment', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_overtime_payment/hr_overtime_payment/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_overtime_payment.listing', {
#             'root': '/hr_overtime_payment/hr_overtime_payment',
#             'objects': http.request.env['hr_overtime_payment.hr_overtime_payment'].search([]),
#         })

#     @http.route('/hr_overtime_payment/hr_overtime_payment/objects/<model("hr_overtime_payment.hr_overtime_payment"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_overtime_payment.object', {
#             'object': obj
#         })
