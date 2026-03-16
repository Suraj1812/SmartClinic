import secrets
import string

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SmartClinicAppointment(models.Model):
    _name = "smart_clinic.appointment"
    _description = "Appointment"
    _order = "appointment_datetime desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    tracking_code = fields.Char(
        string="Tracking Code",
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self._generate_tracking_code(),
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    patient_id = fields.Many2one(
        "smart_clinic.patient",
        string="Patient",
        required=True,
        ondelete="cascade",
        check_company=True,
    )
    doctor_id = fields.Many2one(
        "smart_clinic.doctor",
        string="Doctor",
        required=True,
        ondelete="restrict",
        check_company=True,
    )
    appointment_datetime = fields.Datetime(string="Appointment Date", required=True)
    duration_minutes = fields.Integer(string="Duration (Minutes)", default=30, required=True)
    appointment_end = fields.Datetime(
        string="End Time",
        compute="_compute_appointment_end",
        store=True,
    )
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="pending",
        required=True,
    )
    booking_source = fields.Selection(
        [
            ("backend", "Backend"),
            ("website", "Website"),
        ],
        default="backend",
        required=True,
        readonly=True,
    )
    notes = fields.Text()
    patient_phone = fields.Char(related="patient_id.phone", store=True, readonly=True)
    patient_email = fields.Char(related="patient_id.email", store=True, readonly=True)
    doctor_specialization = fields.Char(
        related="doctor_id.specialization",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        ("tracking_code_unique", "unique(tracking_code)", "Tracking code must be unique."),
    ]

    @api.depends("appointment_datetime", "duration_minutes")
    def _compute_appointment_end(self):
        for appointment in self:
            if appointment.appointment_datetime and appointment.duration_minutes:
                appointment.appointment_end = fields.Datetime.add(
                    appointment.appointment_datetime,
                    minutes=appointment.duration_minutes,
                )
            else:
                appointment.appointment_end = appointment.appointment_datetime

    @api.model
    def _generate_tracking_code(self):
        alphabet = string.ascii_uppercase + string.digits
        for _attempt in range(10):
            code = "".join(secrets.choice(alphabet) for _i in range(10))
            if not self.search_count([("tracking_code", "=", code)]):
                return code
        raise ValidationError(_("Unable to generate a unique tracking code. Please try again."))

    @api.onchange("doctor_id")
    def _onchange_doctor_id(self):
        if self.doctor_id:
            self.duration_minutes = self.doctor_id.consultation_duration
            self.company_id = self.doctor_id.company_id

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("company_id"):
                if vals.get("doctor_id"):
                    vals["company_id"] = self.env["smart_clinic.doctor"].browse(
                        vals["doctor_id"]
                    ).company_id.id
                elif vals.get("patient_id"):
                    vals["company_id"] = self.env["smart_clinic.patient"].browse(
                        vals["patient_id"]
                    ).company_id.id
                else:
                    vals["company_id"] = self.env.company.id
            if not vals.get("name") or vals["name"] == _("New"):
                vals["name"] = sequence.next_by_code("smart_clinic.appointment") or _("New")
            if not vals.get("tracking_code"):
                vals["tracking_code"] = self._generate_tracking_code()
            if not vals.get("duration_minutes") and vals.get("doctor_id"):
                vals["duration_minutes"] = self.env["smart_clinic.doctor"].browse(
                    vals["doctor_id"]
                ).consultation_duration
            vals.setdefault("booking_source", "backend")
        return super().create(vals_list)

    @api.constrains("duration_minutes")
    def _check_duration_minutes(self):
        for appointment in self:
            if appointment.duration_minutes <= 0:
                raise ValidationError(_("Appointment duration must be greater than zero."))

    @api.constrains("patient_id", "doctor_id", "company_id")
    def _check_company_consistency(self):
        for appointment in self:
            if appointment.patient_id and appointment.patient_id.company_id != appointment.company_id:
                raise ValidationError(_("Patient and appointment must belong to the same company."))
            if appointment.doctor_id and appointment.doctor_id.company_id != appointment.company_id:
                raise ValidationError(_("Doctor and appointment must belong to the same company."))

    @api.constrains(
        "doctor_id",
        "appointment_datetime",
        "appointment_end",
        "duration_minutes",
        "status",
    )
    def _check_doctor_schedule(self):
        for appointment in self:
            if (
                not appointment.doctor_id
                or not appointment.appointment_datetime
                or not appointment.appointment_end
                or appointment.status == "cancelled"
            ):
                continue

            conflicting_appointment = self.search(
                [
                    ("id", "!=", appointment.id),
                    ("doctor_id", "=", appointment.doctor_id.id),
                    ("appointment_datetime", "<", appointment.appointment_end),
                    ("appointment_end", ">", appointment.appointment_datetime),
                    ("status", "!=", "cancelled"),
                ],
                limit=1,
            )
            if conflicting_appointment:
                raise ValidationError(
                    _(
                        "This doctor already has an appointment scheduled for the selected date and time."
                    )
                )

    def action_confirm(self):
        self.write({"status": "confirmed"})

    def action_complete(self):
        self.write({"status": "completed"})

    def action_cancel(self):
        self.write({"status": "cancelled"})

    def action_reset_pending(self):
        self.write({"status": "pending"})
