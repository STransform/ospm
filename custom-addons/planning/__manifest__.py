{
    "name": "HR Annual Planning",
    "version": "1.0",
    "author": "Chala Olani",
    'summary': 'HR Annual Planning module',
    "category": "Human Resources",
    "description": "This module allows you to manage the annual planning of your company.",
    "depends": ['base','hr','user_group','custom_notification','web_notify'],
    "data": [
        'security/ir.model.access.xml',
        'security/ir.model.access.csv',
        'views/hr_annual_plan_view.xml',
        'views/hr_strategic_plan_view.xml',
        'views/menu_item_view.xml',
    ],
    "assets":{
        
    },
    "installable": True,
    "auto_install": False,
    "application": True,
    'license': 'LGPL-3'
}