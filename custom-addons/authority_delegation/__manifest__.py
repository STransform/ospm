{
    "name": "Authority Delegation",
    "version": "1.0",
    "summary": "Manage authority delegation among employees.",
    "description": "A module to handle delegation of authority within the organization.",
    "category": "Human Resources",
    "author": "Chala Olani",
    "depends": ["base", "hr","user_group", "custom_notification","web_notify"],
    "data": [
        'security/ir.model.access.csv',
        'views/authority_delegation_view.xml',
        'views/authority_delegation_menu.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    'license': 'LGPL-3'
}
