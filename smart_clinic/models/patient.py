import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SmartClinicPatient(models.Model):
    _name = "smart_clinic.patient"
    _description = "Patient"
    _order = "name"

    name = fields.Char(required=True)
    phone = fields.Char(required=True)
    phone_normalized = fields.Char(compute="_compute_phone_normalized", store=True, index=True)
    email = fields.Char()
    gender = fields.Selection(
        [
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
        ],
        string="Gender",
    )
    date_of_birth = fields.Date()
    address = fields.Text()
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    active = fields.Boolean(default=True)
    appointment_ids = fields.One2many(
        "smart_clinic.appointment",
        "patient_id",
        string="Appointments",
    )
    appointment_count = fields.Integer(compute="_compute_appointment_count")

    @api.depends("appointment_ids")
    def _compute_appointment_count(self):
        for patient in self:
            patient.appointment_count = len(patient.appointment_ids)

    @api.depends("phone")
    def _compute_phone_normalized(self):
        for patient in self:
            patient.phone_normalized = re.sub(r"\D", "", patient.phone or "")

    @api.constrains("date_of_birth")
    def _check_birth_date(self):
        today = fields.Date.to_date(fields.Date.today())
        for patient in self:
            if patient.date_of_birth and patient.date_of_birth > today:
                raise ValidationError(_("Date of birth cannot be in the future."))

    @api.constrains("email")
    def _check_email(self):
        email_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        for patient in self:
            if patient.email and not email_pattern.match(patient.email):
                raise ValidationError(_("Enter a valid patient email address."))

    def action_view_appointments(self):
        action = self.env.ref("smart_clinic.smart_clinic_appointment_action").read()[0]
        if len(self) == 1:
            action["domain"] = [("patient_id", "=", self.id)]
            action["context"] = {
                "default_patient_id": self.id,
                "default_company_id": self.company_id.id,
            }
        return action
