{
    "name": "Transfer Employee",
    "version": "1.0",
    "author": "Chala Olani",
    'summary': "This module is biult for handling the Employee Transfer",
    "category": "Human Resources",
    "description": "This module is biult for handling the Employee Transfer",
    "depends": ['base','hr','user_group','custom_notification','web_notify','web'],
    "data": [
        'security/ir.model.access.csv',
        'security/ir.model.access.xml',
        'views/hr_employee_view.xml',
        'views/transfer_request_views.xml',
        'views/menu_view.xml',
        'report/report.xml',
        'report/template.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    'license': 'LGPL-3'
}