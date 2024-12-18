{
    "name": "Hr Termination",
    "version": "1.0",
    "category": "Human Resources",
    "author" : "Yohanes Mesfin",
    "description": "This module allows you to terminate employees.",
    "depends": ["base", "hr", "mail", "hr_contract", "custom_notification", "user_group"],
    "data":[
        "security/ir.model.access.csv",
        "security/access_rule.xml",
        "views/termination_views.xml",
        "views/menu.xml",
    ],
    'assets': {
    'web.assets_backend': [
        'hr_termination/static/src/**/*',
    ]},
}