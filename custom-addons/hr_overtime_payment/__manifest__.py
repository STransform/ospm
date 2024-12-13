# -*- coding: utf-8 -*-
{
    "name": "hr_overtime_payment",
    "summary": """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    "description": """
        Long description of module's purpose
    """,
    "author": "My Company",
    "website": "https://www.otech.et",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Human Resource",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "hr",
        "mail",
        "hr_contract",
        "user_group",
        "custom_notification",
        "web_notify",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/hr_overtime_type_view.xml",
        "views/hr_overtime_payment_view.xml",
        "views/overtime_reject_reason_view.xml",
        "views/hr_employee_view.xml",
        "views/menu.xml",
        "views/views.xml",
        "views/templates.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
}
