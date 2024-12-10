{
    'name': 'Notification',
    'version': '1.0',
    'description': '''
        This module will give an overview about how to add new menu in navbar 
        using JS.
    ''',
    'category': 'Productivity/Discuss',
    "author": "Chala Olani",
    'depends': ['base','mail','bus','web'],
    'data' :[
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_notification/static/src/js/notification.js',
            'custom_notification/static/src/xml/notification.xml',
        ],
    },
}
