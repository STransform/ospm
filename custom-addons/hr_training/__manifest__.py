{
    'name': "Training",
    'version':'1.0.0', 
    'category': 'Human Resources', 
    'author': "Yohanes Mesfin",
    'depends' : ['hr', 'base', 'web', 'mail', 'bus', 'web_notify'], 
    'data' : [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/dept_request_rule.xml',
        'views/dept_request.xml',
        'views/hr_request.xml',
        'views/menu.xml',
        'data/sequence.xml',
    ], 
    'assets': {
        'web.assets_backend': [
            'hr_training/static/src/**/*',
        ],
    },
    'installable': True, 
}