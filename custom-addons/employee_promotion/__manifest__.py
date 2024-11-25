{
    'name': "Employee Promotion",
    'version': '16.0.1.0.0',
    'category': 'Human Resources',
    'author' : 'Yohanes Mesfin',
    'description': "You may set an employee's promotion using this module. "
                   "Also, the promotion is visible on each employee form .",
    'depends': ['base', 'hr', 'mail', 'hr_contract'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/employee_promotion_views.xml',
        'views/promotion_type_views.xml',
        'views/hr_employee_views.xml',
        'views/employee_promotion_approved.xml',
        'report/employee_promotion_report.xml',
        'report/employee_promotion_template.xml', 
        'views/internal_vacancy.xml',
        'views/appilications.xml', 
        'views/shortlisted.xml',
        'views/ceo_approved.xml',
        'views/promotion_minutes.xml',


    ],

    'assets': {
    'web.assets_common': [
        'employee_promotion/static/src/css/kanban-ribbon.css'
    ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}