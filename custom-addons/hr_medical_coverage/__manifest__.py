{
    'name': "Medical Coverage Action",
    'version':'16.0.0', 
    'category': 'Generic Modules/Human Resources', 
    'author': "Kuma Telila",
    'depends' : ['hr', 'base'], 
    'data' : [
        'security/hr_medical_coverage_group.xml',
        'security/ir.model.access.csv', 
        'views/medical_coverage.xml', 
        'views/menu.xml', 
    ], 
    'assets': {
        'web.assets_backend': [
            'hr_medical_coverage/static/src/**/*',
        ]},
    'installable': True, 
    'application': False,
}