{
    'name': "Recruitment Request", 
    'version':'1.0.0', 
    'category': 'Human Resources', 
    'author': "Simon & Yohanes",
    'depends' : ['hr', 'base', 'web', 'mail', 'bus', 'hr_recruitment'], 
    'installable': True, 
    'data': [
        "views/recruitment_request_view.xml",
        "views/menu.xml",
        "security/ir.model.access.csv",
        "security/groups.xml",
    ]
}