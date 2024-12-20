{
    'name': "Training",
    'version':'1.0.0', 
    'category': 'Human Resources', 
    'author': "Yohanes Mesfin",
    'depends' : ['hr', 'base', 'web', 'mail', 'bus', 'web_notify', 'user_group','custom_notification'], 
    'data' : [
        'security/ir.model.access.csv',
        'security/dept_request_rule.xml',
        'views/dept_request.xml',
        'views/hr_request.xml',
        'views/menu.xml',
        'data/sequence.xml',
        'report/report.xml',
        'report/template.xml',
        'report/template_for_hr.xml'
    ], 
    'assets': {
        'web.assets_backend': [
            'hr_training/static/src/**/*',
        ],
    },
    'installable': True, 
}