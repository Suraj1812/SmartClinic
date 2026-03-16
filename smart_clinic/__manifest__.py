{
    "name": "Smart Clinic Appointment Management",
    "summary": "Manage patients, doctors, and appointments for a clinic.",
    "description": """
Smart Clinic is a beginner-friendly Odoo module for managing
patient records, doctor profiles, and appointment bookings.
It also includes public website pages for doctor listing,
appointment booking, and appointment status lookup.
""",
    "version": "17.0.1.0.0",
    "category": "Healthcare",
    "author": "OpenAI Codex",
    "license": "LGPL-3",
    "depends": ["base", "website"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/patient_views.xml",
        "views/doctor_views.xml",
        "views/appointment_views.xml",
        "views/menu_views.xml",
        "views/website_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "smart_clinic/static/src/css/website.css",
        ],
    },
    "application": True,
    "installable": True,
}
