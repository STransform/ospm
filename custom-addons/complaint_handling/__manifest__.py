# complaint_handling_management/__manifest__.py
{
    'name': 'Complaint handling management',
    'version': '16.0.1.0.0',
    'summary': 'Manages employee complaints regarding HR or Discipline Committee decisions.',
    'description': """A module for handling employee complaints, enabling escalation to legal service, CEO, and court.""",
    'author': 'Simon Temesgen',
    'depends': ['base', 'hr','user_group','custom_notification','web','web_notify'],
    'data': [
        # 'security/groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/complaint_views.xml',
        "report/report.xml",  
        "report/template.xml",
    ],
    'installable': True,
    'application': True,
}