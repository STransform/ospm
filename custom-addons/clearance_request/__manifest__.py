{
    "name": "Employee Clearance",
    "version": "16.0.1.0",
    "depends": ["hr", "mail", "base",'user_group','custom_notification','web','web_notify'],
    "author": "Simon Temesgen",
    "category": "Human Resources",
    "summary": "Manage employee clearance workflows",
    "description": """
Employee Clearance Workflow:
- Department/Service, Property Administration, Finance, and HR Office approvals.
""",
    "data": [
        # "security/clearance_security.xml",  # Group definitions MUST come first
        "security/record_rule.xml",
        "security/ir.model.access.csv",  # Access rights should come after groups
        "views/clearance_views.xml",    
        "report/report.xml",  
        "report/template.xml",
       
    ],
    "installable": True,
    "application": False,
}
