from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import SavepointCase


class TestSmartClinicModels(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.patient = cls.env["smart_clinic.patient"].create(
            {
                "name": "John Carter",
                "phone": "+1 (555) 200-3000",
                "email": "john.carter@example.com",
                "company_id": cls.company.id,
            }
        )
        cls.doctor = cls.env["smart_clinic.doctor"].create(
            {
                "name": "Dr. Amelia Stone",
                "specialization": "Cardiology",
                "email": "amelia.stone@example.com",
                "consultation_duration": 45,
                "company_id": cls.company.id,
            }
        )

    def test_patient_phone_is_normalized(self):
        self.assertEqual(self.patient.phone_normalized, "15552003000")

    def test_appointment_defaults_are_applied(self):
        appointment_start = fields.Datetime.to_datetime(fields.Datetime.now()) + timedelta(days=1)
        appointment = self.env["smart_clinic.appointment"].create(
            {
                "patient_id": self.patient.id,
                "doctor_id": self.doctor.id,
                "appointment_datetime": fields.Datetime.to_string(appointment_start),
            }
        )

        self.assertTrue(appointment.name.startswith("APT/"))
        self.assertEqual(appointment.company_id, self.company)
        self.assertEqual(appointment.duration_minutes, 45)
        self.assertEqual(appointment.booking_source, "backend")
        self.assertTrue(appointment.tracking_code)

    def test_doctor_overlap_is_blocked(self):
        start = fields.Datetime.to_datetime(fields.Datetime.now()) + timedelta(days=2)
        self.env["smart_clinic.appointment"].create(
            {
                "patient_id": self.patient.id,
                "doctor_id": self.doctor.id,
                "appointment_datetime": fields.Datetime.to_string(start),
                "duration_minutes": 45,
            }
        )

        with self.assertRaises(ValidationError):
            self.env["smart_clinic.appointment"].create(
                {
                    "patient_id": self.patient.id,
                    "doctor_id": self.doctor.id,
                    "appointment_datetime": fields.Datetime.to_string(
                        start + timedelta(minutes=15)
                    ),
                    "duration_minutes": 30,
                }
            )

    def test_cancelled_appointment_does_not_block_new_slot(self):
        start = fields.Datetime.to_datetime(fields.Datetime.now()) + timedelta(days=3)
        appointment = self.env["smart_clinic.appointment"].create(
            {
                "patient_id": self.patient.id,
                "doctor_id": self.doctor.id,
                "appointment_datetime": fields.Datetime.to_string(start),
                "duration_minutes": 30,
            }
        )
        appointment.action_cancel()

        replacement = self.env["smart_clinic.appointment"].create(
            {
                "patient_id": self.patient.id,
                "doctor_id": self.doctor.id,
                "appointment_datetime": fields.Datetime.to_string(start),
                "duration_minutes": 30,
            }
        )

        self.assertEqual(replacement.status, "pending")

    def test_future_date_of_birth_is_rejected(self):
        future_dob = fields.Date.to_date(fields.Date.today()) + timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.env["smart_clinic.patient"].create(
                {
                    "name": "Invalid Patient",
                    "phone": "5551234567",
                    "date_of_birth": fields.Date.to_string(future_dob),
                    "company_id": self.company.id,
                }
            )
