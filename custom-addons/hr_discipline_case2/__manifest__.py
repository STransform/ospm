{
    'name': 'Discipline Case',
    'version': '1.0',
    'category': 'Human Resources',
    'author': 'Simon Temesten',
    'website': 'OTech',
    'depends': ['base', 'hr','user_group','custom_notification','web','web_notify'],  # Dependencies on base and hr modules
    'data': [
        # 'security/record_rule.xml',
        'security/ir.model.access.csv',
        'views/discipline_case_views.xml',
        "report/report.xml",  
        "report/template.xml",
    ],
    'installable': True,
    'application': True,
}
