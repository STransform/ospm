from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrMedicalOrganization(models.Model):
    _name = "hr.medical.coverage.organization"
    _description = "Medical Coverage Oraganization"
    _inherit = "mail.thread"
    _order = "create_date desc"

    name = fields.Char(string="Institution Name", required=True, tracking=True)
    location = fields.Char(string="Location", required=True, tracking=True)
    phone_number = fields.Char(string="Phone Number", required=True, tracking=True)
    organization_type = fields.Selection(
        string="Institution Type",
        selection=[
            ("governmental", "Governmental"),
            ("private", "Private"),
        ],
        required=True,
         tracking=True
    )
    organization_category = fields.Selection(
        string="Institution Category",
        selection=[
            ("hospital", "Hospital"),
            ("clinic", "Clinic"),
            ("pharmacy", "Pharmacy"),
        ],
        required=True, tracking=True
    )
    email_address = fields.Char(string="Email Address", required=True, tracking=True)
    tax_id_number = fields.Char(string="Tax ID Number", tracking=True)
    emergency_contact_phone = fields.Char(string="Emergency Contact Phone", tracking=True)
    website = fields.Char(string="Website", tracking=True)
