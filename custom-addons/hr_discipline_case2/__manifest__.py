{
    'name': 'Discipline Case',
    'version': '1.0',
    'category': 'Human Resources',
    'author': 'Simon Temesten',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'hr','user_group','custom_notification','web_notify'],  # Dependencies on base and hr modules
    'data': [
        # 'security/groups.xml',
        'security/ir.model.access.csv',
        'views/discipline_case_views.xml',
    ],
    'installable': True,
    'application': True,
}
