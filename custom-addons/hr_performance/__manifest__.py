# -*- coding: utf-8 -*-
{
    'name': 'hr_performance',
    'version': '',
    'summary': """ hr_performance Summary """,
    'author': 'Kuma Telila @otech',
    'website': 'www.otech.et',
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'survey', 'mail', 'custom_notification', 'web_notify', 'user_group'],
    'data': [
        "security/hr_performance_group.xml",
        "security/ir.model.access.csv",
        "views/performance_measure_views.xml",
        "views/report.xml",
        "views/menu.xml",
        
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
