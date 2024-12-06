{
    'name': 'HR Retirement Management',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Manage employee retirements dynamically based on company policies.',
    'description': """
        A module to handle employee retirement requests, approvals, and dynamic configuration settings.
    """,
    'author': 'Chala Olani',
    'depends': ['hr','base','planning'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_retirement_settings_data.xml',
        'data/cron_job.xml',
        'views/hr_retirement_settings_views.xml',
        'views/hr_employee_views.xml',
        'views/early_retirement_request_views.xml',
        'views/retirement_request_views.xml',
        'views/extension_request_views.xml',
        'views/menu.views.xml',
    ],
    'post_init_hook': 'update_near_retirement_post_install',
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
