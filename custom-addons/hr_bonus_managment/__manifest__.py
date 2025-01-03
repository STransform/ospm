# -*- coding: utf-8 -*-
{
    "name": "hr_bonus_managment",
    "version": "16.0.1.0.0",
    "summary": """ Hr_bonus_managment Summary """,
    "author": "Kuma Telila@otech",
    "website": "https://otech.et",
    "category": "Human Resource",
    "depends": [
        "base",
        "mail",
        "hr",
        "hr_performance",
        "hr_pay_grade",
        "custom_notification",
        "web_notify",
        "user_group",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_bonus_managment_view.xml",
        "views/hr_employee_view.xml",
        "views/menu.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
