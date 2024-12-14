{
    "name": "Employee Clearance",
    "version": "16.0.1.0",
    "depends": ["hr", "mail"],
    "author": "Simon Temesgen",
    "category": "Human Resources",
    "summary": "Manage employee clearance workflows",
    "description": """
Employee Clearance Workflow:
- Department/Service, Property Administration, Finance, and HR Office approvals.
""",
    "data": [
        "views/clearance_views.xml",
        "security/ir.model.access.csv",
        "security/record_rule.xml",
        "security/clearance_security.xml",
    ],
    "installable": True,
    "application": False,
}
