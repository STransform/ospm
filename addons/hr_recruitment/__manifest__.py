# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Recruitment',
    'version': '1.1',
    'category': 'Human Resources/Recruitment',
    'sequence': 90,
    'summary': 'Track your recruitment pipeline',
    'website': 'https://www.odoo.com/app/recruitment',
    'depends': [
        'hr',
        'calendar',
        'utm',
        'attachment_indexation',
        'web_tour',
        'digest',
        'hr_recruitment_request'
    ],
    'data': [
        'security/hr_recruitment_security.xml',
        'security/ir.model.access.csv',
        'data/digest_data.xml',
        'data/mail_alias_data.xml',
        'data/mail_message_subtype_data.xml',
        'data/mail_template_data.xml',
        'data/mail_templates.xml',
        'data/hr_recruitment_data.xml',
        'views/hr_recruitment_views.xml',
        'views/res_config_settings_views.xml',
        'views/hr_department_views.xml',
        'views/hr_job_views.xml',
        'views/mail_activity_views.xml',
        'views/digest_views.xml',
        'wizard/applicant_refuse_reason_views.xml',
        'wizard/applicant_approve_reason.xml',
        'wizard/applicant_refuse_reason.xml',
        #'views/hr_approval_reason_views.xml',
   
        'wizard/applicant_send_mail_views.xml',
        

    ],
    'demo': [
        'data/hr_recruitment_demo.xml',
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'hr_recruitment/static/src/**/*.js',
            'hr_recruitment/static/src/**/*.scss',
            'hr_recruitment/static/src/**/*.css',
            'hr_recruitment/static/src/**/*.xml',
            'hr_recruitment/static/src/js/tours/hr_recruitment.js',
            'hr_recruitment/static/src/js/tours/cgpa_filter.js',
        ],
    },
    'license': 'LGPL-3',
}
