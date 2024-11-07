{
    'name': "Training",
    'version':'1.0.0', 
    'category': 'Human Resources', 
    'author': "yohanes Mesfin",
    'depends' : ['hr', 'base', 'web', 'mail'], 
    'data' : [
        'views/training_view.xml', 
        'views/menu.xml', 
        'security/ir.model.access.csv',
        'security/groups.xml',
    ], 

    'assets': {
        'web.assets_backend': [
            'hr_training/static/src/**/*',
        ],
    },
    'installable': True, 
}