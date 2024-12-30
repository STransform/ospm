{
    'name' : "Attendance Remark",
    'version':'1.0.0',
    'category': 'Human Resources',
    'author': 'Yohanes Mesfin',
    'depends' : ['hr', 'hr_attendance', 'base', 'web', 'mail', 'bus', 'web_notify', 'user_group','custom_notification'],
    'data' : [
        'security/ir.model.access.csv',
        'security/remark_access_rule.xml',
        'views/attendance_remark.xml',
        #'views/menu.xml',
    ],
    
}