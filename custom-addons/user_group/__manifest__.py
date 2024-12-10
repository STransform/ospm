{
    "name": "User Group",
    "version": "1.0",
    "author": "Chala Olani",
    'summary': 'Manage User Groups in Odoo',
    "category": "Human Resources",
    "description": """ The User Group module allows you to define and manage 
            user groups with specific access rights and permissions in Odoo. """,
    "depends": ['base'],
    "data": [
        'security/user_group.xml'
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    'license': 'LGPL-3'
}