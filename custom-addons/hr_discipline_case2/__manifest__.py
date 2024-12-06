{
    'name': 'Discipline Case',
    'version': '1.0',
    'category': 'Human Resources',
    'author': 'Simon Temesten',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'hr'],  # Dependencies on base and hr modules
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/discipline_case_views.xml',
    ],
    'installable': True,
    'application': True,
}
