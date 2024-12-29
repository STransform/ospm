{
    'name': "Medical Coverage Action",
    'version':'16.0.0', 
    'category': 'Generic Modules/Human Resources', 
    'author': "Kuma Telila",
    'depends' : ['hr', 'base', 'mail','user_group', 'custom_notification','web_notify'], 
    'data' : [
        'security/hr_medical_coverage_group.xml',
        'security/ir.model.access.csv', 
        'views/medical_coverage.xml', 
        'views/medical_coverage_organization.xml',
        'views/medical_pre_request.xml',
        'views/menu.xml', 
    ], 
    'assets': {
        'web.assets_backend': [
            'hr_medical_coverage/static/src/**/*',
        ]},
    'installable': True, 
    'application': False,
}