{
    "name": "Sales User",
    "version": "1.0",
    "author": "Simon Temesgen",
    'summary': 'Manage User Groups in Sales Management System',
    "category": "Sales Category",
    "description": """ This module enables the assignment of roles and permissions to users in the Sales Management System. """,
    "depends": ['base'],
    "data": [
        'security/sales_user.xml'
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    'license': 'LGPL-3'
}