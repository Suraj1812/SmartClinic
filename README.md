# SmartClinic Appointment Management System

SmartClinic is a production-minded Odoo 17 module for clinics and small hospitals.
It manages patient records, doctor schedules, and appointment booking through both
the Odoo backend and a public website.

## What is included

- Odoo models for `Patient`, `Doctor`, and `Appointment`
- Public website pages for:
  - Home
  - Doctors
  - Book Appointment
  - Appointment Status
- Admin dashboard menus for managing records inside Odoo
- Multi-company aware security groups and record rules
- Public booking hardening with safer patient matching
- Verified status lookup using tracking code plus patient phone number
- Appointment overlap protection with configurable consultation duration
- Docker-based local deployment stack
- GitHub Actions validation for Python and XML syntax
- Odoo model tests for core business rules

## Project structure

```text
.
|-- .env.example
|-- .github/workflows/validate.yml
|-- .gitignore
|-- Makefile
|-- config/odoo.conf
|-- docker-compose.yml
|-- README.md
`-- smart_clinic/
    |-- __manifest__.py
    |-- controllers/
    |   `-- main.py
    |-- data/
    |   `-- sequence.xml
    |-- models/
    |   |-- appointment.py
    |   |-- doctor.py
    |   `-- patient.py
    |-- security/
    |   |-- ir.model.access.csv
    |   `-- security.xml
    |-- static/
    |   `-- src/css/website.css
    |-- tests/
    |   `-- test_models.py
    `-- views/
        |-- appointment_views.xml
        |-- doctor_views.xml
        |-- menu_views.xml
        |-- patient_views.xml
        `-- website_templates.xml
```

## Production-ready improvements

- Website booking only shows doctors marked as available and published
- Public patient creation no longer overwrites existing patient details loosely
- Status lookup requires both the appointment tracking code and phone number
- All records are scoped by company using Odoo record rules
- Staff and managers have separate access groups
- Appointments block overlapping time slots instead of only exact duplicates
- Consultation duration is configurable per doctor and flows into appointments
- Automated syntax validation is included for GitHub

## Quick start with Docker

1. Copy `.env.example` to `.env`.
2. Update the database and password values.
3. Start the stack:

```bash
docker compose up -d
```

4. Open `http://localhost:8069`.
5. Install or update the `smart_clinic` module if it is not already installed.

## Manual Odoo installation

1. Copy the `smart_clinic` folder into your Odoo custom addons path.
2. Ensure the `website` module is installed.
3. Restart Odoo.
4. Update the Apps list.
5. Install `Smart Clinic Appointment Management`.

## Backend usage

1. Assign users to `Smart Clinic User` or `Smart Clinic Manager`.
2. Create doctor profiles and set:
   - consultation duration
   - website visibility
   - availability
3. Review incoming website bookings from the `Appointments` menu.
4. Change status to `Confirmed`, `Completed`, or `Cancelled`.

## Website usage

- `/smart-clinic` shows the clinic landing page
- `/smart-clinic/doctors` lists published doctors
- `/smart-clinic/book` accepts appointment bookings
- `/smart-clinic/status` checks appointment status using tracking code and phone number

## Validation

Local validation used for this repo:

- `python3 -m compileall smart_clinic`
- `xmllint --noout` on all XML files

## Notes

- The module targets Odoo `17.0`.
- The repository currently ships without demo data so production teams can load real clinic data cleanly.
- Running full Odoo integration tests requires an Odoo runtime, which is not bundled inside this workspace.
