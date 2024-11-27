from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrMedicalOrganization(models.Model):
    _name = "hr.medical.coverage.organization"
    _description = "Medical Coverage Oraganization"
    _order = "create_date desc"

    name = fields.Char(string="Organization Name", required=True)
    location = fields.Char(string="Location", required=True)
    phone_number = fields.Char(string="Phone Number", required=True)
    organization_type = fields.Selection(
        string="Organization Type",
        selection=[
            ("hospital", "Hospital"),
            ("clinic", "Clinic"),
            ("pharmacy", "Pharmacy"),
        ],
        required=True,
    )
    email_address = fields.Char(string="Email Address", required=True)
    tax_id_number = fields.Char(string="Tax ID Number")
    emergency_contact_phone = fields.Char(string="Emergency Contact Phone")
    website = fields.Char(string="Website")
