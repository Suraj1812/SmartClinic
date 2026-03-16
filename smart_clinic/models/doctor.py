import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SmartClinicDoctor(models.Model):
    _name = "smart_clinic.doctor"
    _description = "Doctor"
    _order = "name"

    name = fields.Char(required=True)
    specialization = fields.Char(required=True)
    phone = fields.Char()
    email = fields.Char()
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    availability_note = fields.Char(string="Availability")
    bio = fields.Text()
    image_1920 = fields.Image(string="Photo")
    is_available = fields.Boolean(default=True)
    website_published = fields.Boolean(string="Visible on Website", default=True)
    consultation_duration = fields.Integer(default=30, required=True)
    active = fields.Boolean(default=True)
    appointment_ids = fields.One2many(
        "smart_clinic.appointment",
        "doctor_id",
        string="Appointments",
    )
    appointment_count = fields.Integer(compute="_compute_appointment_count")

    _sql_constraints = [
        (
            "doctor_email_company_unique",
            "unique(company_id, email)",
            "Doctor email must be unique per company.",
        ),
    ]

    @api.depends("appointment_ids")
    def _compute_appointment_count(self):
        for doctor in self:
            doctor.appointment_count = len(doctor.appointment_ids)

    @api.constrains("email")
    def _check_email(self):
        email_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        for doctor in self:
            if doctor.email and not email_pattern.match(doctor.email):
                raise ValidationError(_("Enter a valid doctor email address."))

    @api.constrains("consultation_duration")
    def _check_consultation_duration(self):
        for doctor in self:
            if doctor.consultation_duration <= 0:
                raise ValidationError(_("Consultation duration must be greater than zero."))

    def action_view_appointments(self):
        action = self.env.ref("smart_clinic.smart_clinic_appointment_action").read()[0]
        if len(self) == 1:
            action["domain"] = [("doctor_id", "=", self.id)]
            action["context"] = {
                "default_doctor_id": self.id,
                "default_company_id": self.company_id.id,
                "default_duration_minutes": self.consultation_duration,
            }
        return action
