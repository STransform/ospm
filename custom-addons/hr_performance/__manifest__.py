# -*- coding: utf-8 -*-
{
    'name': 'hr_performance',
    'version': '',
    'summary': """ hr_performance Summary """,
    'author': '',
    'website': '',
    'category': '',
    'depends': ['base', 'hr', 'survey'],
    'data': [
        "security/hr_performance_group.xml",
        "security/ir.model.access.csv",
        "views/performance_measure_views.xml",
        "views/menu.xml",
        
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
