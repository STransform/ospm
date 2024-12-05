# -*- coding: utf-8 -*-
{
    'name': 'Hr_salary_increment',
    'version': '',
    'summary': """ Hr_salary_increment Summary """,
    'author': 'Kuma Telila @otech',
    'website': 'https://otech.et',
    'category': 'Human Resource',
    'depends': ['base', 'hr','hr_pay_grade', 'mail', 'hr_contract', 'hr_performance'],
    'data': [
        "security/ir.model.access.csv",
        "data/cron_job.xml",
        "views/hr_salary_increment_view.xml",
        "views/menu.xml",
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
