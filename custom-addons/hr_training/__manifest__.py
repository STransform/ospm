{
    'name': "Training",
    'version':'1.0.0', 
    'category': 'Human Resources', 
    'author': "yohanes Mesfin",
    'depends' : ['hr', 'base', 'web', 'mail', 'bus', 'web_notify'], 
    'data' : [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'security/dept_request_rule.xml',
        'views/training_view.xml', 
        'views/dept_request.xml',
        'views/hr_request.xml',
        'views/menu.xml', 
    ], 

    'assets': {
        'web.assets_backend': [
            'hr_training/static/src/**/*',
        ],
    },
    'installable': True, 
}