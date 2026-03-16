from datetime import datetime
import re

from odoo import fields, http
from odoo.exceptions import ValidationError
from odoo.http import request


class SmartClinicWebsite(http.Controller):
    @staticmethod
    def _normalize_phone(phone):
        return re.sub(r"\D", "", phone or "")

    @staticmethod
    def _website_company():
        return request.website.company_id or request.env.company

    def _booking_page_values(self, form_data=None, error=None):
        company = self._website_company()
        doctor_model = request.env["smart_clinic.doctor"].sudo()
        doctors = doctor_model.search(
            [
                ("company_id", "=", company.id),
                ("active", "=", True),
                ("is_available", "=", True),
                ("website_published", "=", True),
            ]
        )
        specialties = sorted({specialty for specialty in doctors.mapped("specialization") if specialty})
        return {
            "company_name": company.name,
            "doctors": doctors,
            "doctor_count": doctor_model.search_count(
                [("company_id", "=", company.id), ("active", "=", True), ("website_published", "=", True)]
            ),
            "specialties": specialties,
            "form_data": form_data or {},
            "error": error,
        }

    def _find_or_create_patient(self, values, company):
        patient_model = request.env["smart_clinic.patient"].sudo()
        phone = (values.get("phone") or "").strip()
        normalized_phone = self._normalize_phone(phone)
        email = values.get("email")

        patient = False
        if normalized_phone:
            patient = patient_model.search(
                [
                    ("company_id", "=", company.id),
                    ("phone_normalized", "=", normalized_phone),
                    ("name", "=ilike", values.get("name")),
                ],
                limit=1,
            )
        if not patient and email:
            patient = patient_model.search(
                [
                    ("company_id", "=", company.id),
                    ("email", "=ilike", email),
                    ("name", "=ilike", values.get("name")),
                ],
                limit=1,
            )

        patient_vals = {
            "name": values.get("name"),
            "phone": phone,
            "email": email,
            "gender": values.get("gender"),
            "company_id": company.id,
        }

        if patient:
            # Public booking only fills blank profile details; it does not overwrite
            # an existing patient record with new personal information.
            updates = {
                key: value
                for key, value in patient_vals.items()
                if key != "company_id" and value and not patient[key]
            }
            if updates:
                patient.write(updates)
            return patient

        return patient_model.create(patient_vals)

    @http.route(
        "/",
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def smart_clinic_root_redirect(self, **kwargs):
        return request.redirect("/smart-clinic")

    @http.route(
        ["/smart-clinic", "/smart-clinic/home"],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def smart_clinic_home(self, **kwargs):
        company = self._website_company()
        doctor_model = request.env["smart_clinic.doctor"].sudo()
        patient_model = request.env["smart_clinic.patient"].sudo()
        appointment_model = request.env["smart_clinic.appointment"].sudo()
        featured_doctors = doctor_model.search(
            [
                ("company_id", "=", company.id),
                ("active", "=", True),
                ("is_available", "=", True),
                ("website_published", "=", True),
            ],
            limit=6,
        )

        values = {
            "company_name": company.name,
            "doctors": featured_doctors,
            "doctor_count": doctor_model.search_count(
                [("company_id", "=", company.id), ("active", "=", True)]
            ),
            "available_doctor_count": doctor_model.search_count(
                [
                    ("company_id", "=", company.id),
                    ("active", "=", True),
                    ("is_available", "=", True),
                    ("website_published", "=", True),
                ]
            ),
            "patient_count": patient_model.search_count(
                [("company_id", "=", company.id), ("active", "=", True)]
            ),
            "appointment_count": appointment_model.search_count(
                [("company_id", "=", company.id)]
            ),
            "featured_specialties": sorted(
                {
                    specialty
                    for specialty in featured_doctors.mapped("specialization")
                    if specialty
                }
            )[:4],
        }
        return request.render("smart_clinic.smart_clinic_homepage", values)

    @http.route(
        "/smart-clinic/doctors",
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def smart_clinic_doctors(self, **kwargs):
        company = self._website_company()
        doctors = request.env["smart_clinic.doctor"].sudo().search(
            [
                ("company_id", "=", company.id),
                ("active", "=", True),
                ("website_published", "=", True),
            ]
        )
        return request.render(
            "smart_clinic.smart_clinic_doctors_page",
            {
                "company_name": company.name,
                "doctors": doctors,
                "doctor_count": len(doctors),
                "available_doctor_count": len(doctors.filtered("is_available")),
                "specialties": sorted(
                    {specialty for specialty in doctors.mapped("specialization") if specialty}
                ),
            },
        )

    @http.route(
        "/smart-clinic/book",
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def smart_clinic_book(self, **kwargs):
        return request.render(
            "smart_clinic.smart_clinic_book_page",
            self._booking_page_values(form_data=kwargs),
        )

    @http.route(
        "/smart-clinic/book/submit",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def smart_clinic_book_submit(self, **post):
        company = self._website_company()
        form_data = {key: (value.strip() if isinstance(value, str) else value) for key, value in post.items()}
        required_fields = {
            "patient_name": "patient name",
            "phone": "phone number",
            "doctor_id": "doctor",
            "appointment_datetime": "appointment date and time",
        }
        missing = [
            label for field_name, label in required_fields.items() if not form_data.get(field_name)
        ]
        if missing:
            error = "Please fill in: %s." % ", ".join(missing)
            return request.render(
                "smart_clinic.smart_clinic_book_page",
                self._booking_page_values(form_data=form_data, error=error),
            )

        try:
            doctor_id = int(form_data["doctor_id"])
        except (TypeError, ValueError):
            return request.render(
                "smart_clinic.smart_clinic_book_page",
                self._booking_page_values(form_data=form_data, error="Please choose a valid doctor."),
            )

        doctor = request.env["smart_clinic.doctor"].sudo().browse(doctor_id)
        if (
            not doctor.exists()
            or doctor.company_id != company
            or not doctor.active
            or not doctor.is_available
            or not doctor.website_published
        ):
            return request.render(
                "smart_clinic.smart_clinic_book_page",
                self._booking_page_values(
                    form_data=form_data,
                    error="The selected doctor is not available for online booking.",
                ),
            )

        try:
            appointment_dt = datetime.strptime(
                form_data["appointment_datetime"], "%Y-%m-%dT%H:%M"
            )
        except (TypeError, ValueError):
            return request.render(
                "smart_clinic.smart_clinic_book_page",
                self._booking_page_values(
                    form_data=form_data,
                    error="Please enter a valid appointment date and time.",
                ),
            )

        if appointment_dt <= datetime.now():
            return request.render(
                "smart_clinic.smart_clinic_book_page",
                self._booking_page_values(
                    form_data=form_data,
                    error="Please choose an appointment time in the future.",
                ),
            )

        patient = self._find_or_create_patient(
            {
                "name": form_data.get("patient_name"),
                "phone": form_data.get("phone"),
                "email": form_data.get("email"),
                "gender": form_data.get("gender"),
            },
            company,
        )

        appointment_vals = {
            "company_id": company.id,
            "patient_id": patient.id,
            "doctor_id": doctor.id,
            "appointment_datetime": fields.Datetime.to_string(appointment_dt),
            "duration_minutes": doctor.consultation_duration,
            "booking_source": "website",
            "notes": form_data.get("notes"),
        }
        try:
            appointment = request.env["smart_clinic.appointment"].sudo().create(appointment_vals)
        except ValidationError as error:
            return request.render(
                "smart_clinic.smart_clinic_book_page",
                self._booking_page_values(form_data=form_data, error=str(error)),
            )

        return request.render(
            "smart_clinic.smart_clinic_status_page",
            {
                "appointment": appointment,
                "tracking_code": appointment.tracking_code,
                "phone": patient.phone,
                "booked": True,
                "searched": True,
                "verified": True,
                "error": False,
            },
        )

    @http.route(
        "/smart-clinic/status",
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def smart_clinic_status(self, tracking_code=None, phone=None, booked=None, **kwargs):
        company = self._website_company()
        appointment = False
        normalized_code = (tracking_code or "").strip().upper()
        normalized_phone = self._normalize_phone(phone)
        error = False
        verified = False

        if normalized_code and normalized_phone:
            appointment = request.env["smart_clinic.appointment"].sudo().search(
                [
                    ("company_id", "=", company.id),
                    ("tracking_code", "=", normalized_code),
                    ("patient_id.phone_normalized", "=", normalized_phone),
                ],
                limit=1,
            )
            verified = bool(appointment)
        elif normalized_code or normalized_phone:
            error = "Enter both the tracking code and the patient's phone number."

        values = {
            "appointment": appointment,
            "tracking_code": normalized_code,
            "phone": phone or "",
            "booked": booked == "1",
            "searched": bool(normalized_code or normalized_phone),
            "verified": verified,
            "error": error,
        }
        return request.render("smart_clinic.smart_clinic_status_page", values)
