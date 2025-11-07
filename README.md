# Proiect Payroll System
This repository contains a small payroll web application (Django + DRF backend, Vite + React frontend) used for generating and sending monthly payslips and aggregated CSV reports. It supports bonuses, attendance-based prorated salary calculations, idempotent actions (Idempotency-Key), and structured request logging.

## Quick summary
- Backend: Django (DRF) with services organized under `app/services` and routers under `app/api/routers`.
- Frontend: Vite + React in `frontend/` with simple admin dashboard at `frontend/src/pages/Dashboard.tsx`.
- Persistence: PostgreSQL expected in production (Docker compose used during development/testing).

## Getting started (development)
These are minimal steps to get the project running locally for development. Adjust environment variables as needed.

Prerequisites
- Python 3.11+
- Node 16+ (for frontend dev)
- Docker / Docker Compose (optional but recommended)

1) Create a virtual environment and install backend dependencies

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r rquirements.txt
```

2) Run database migrations and create a superuser (if using a local DB)

```powershell
python manage.py migrate
python manage.py createsuperuser
```

3) Start the backend server (development)

```powershell
python manage.py runserver
```

4) Start the frontend (development)

```powershell
cd frontend
npm install
npm run dev
```

Alternatively you can use Docker compose if a `docker-compose.yml` is available in the project (recommended for reproducible environments).

## Important project files
- `app/api/routers/` — Django REST endpoints (generate/send payslips, bonuses, aggregates, managers).
- `app/services/` — business logic and helper services (pdf/csv generation, salary computations, idempotency, email provider wrappers).
- `app/db/models/` — Django models (Employee, Bonus, Attendance, Department, etc.).
- `frontend/src/pages/Dashboard.tsx` — main admin dashboard UI used in development.

## Notable endpoints
Here are common endpoints used by the frontend and for manual testing. All endpoints expect authenticated requests (JWT) unless noted.

- POST `/api/auth/login/` — obtain auth token
- POST `/api/auth/logout/` — revoke token (best-effort)
- GET `/api/auth/me/` — fetch current user profile
- POST `/api/employees/<id>/generate_pdf/` — generate & save payslip PDF for employee `<id>` (Idempotency-Key supported)
- POST `/api/employees/<id>/send_payslip/` — send payslip email for employee `<id>` (Idempotency-Key supported)
- POST `/api/employees/<id>/generate_aggregate/` — generate & save aggregated CSV for employee `<id>`
- POST `/api/employees/send_payslip_email/` — send payslip via email by employee_id in payload (Idempotency-Key supported)
- POST `/api/bonuses/create/` — create a bonus for an employee
- GET `/api/bonuses/list/?employee_id=<id>` — list bonuses (admin: all, manager: department, employee: own)

### Manager / batch endpoints
These endpoints are used by managers (or admins) to generate and send batch reports for employees or teams. They are important for payroll operations:

- POST `/api/employees/create_aggregated_employee_data/` (or `/createAggregatedEmployeeData`) — Generates the Excel/CSV aggregated report for a single employee for a given period. Use query/body `year` and `month` to specify the period (defaults to current month when omitted).
- POST `/api/employees/send_aggregated_employee_data/` (or `/sendAggregatedEmployeeData`) — Sends the previously-generated aggregated Excel/CSV report via email to the employee. The CSV must be generated and saved first.
- POST `/api/employees/create_pdf_for_employees/` (or `/createPdfForEmployees`) — Generates individual PDF payslips for an employee (or uses endpoint that accepts `employee_id`) and saves them to `media/payslips/<year>-<month>/`.
- POST `/api/employees/send_pdf_to_employees/` (or `/sendPdfToEmployees`) — Sends the generated PDF payslips to employees via email. Supports `Idempotency-Key` to avoid duplicate sends on retries.

Note: endpoint path names may be slightly different depending on router naming; check `app/api/routers/` for exact route strings in your local checkout. The frontend client helpers (in `frontend/src/api/client.ts`) provide convenient wrappers for the common calls.

RBAC notes
- Admin users can act on any employee.
- Managers can only act on their direct reports. 
- Employees may act on themselves.

Idempotency
- Actions that generate or send artifacts support an `Idempotency-Key` header. The backend stores idempotency records scoped to the owner performing the action so retries won't create duplicate sends/generations.
- Client recommendation: generate UUID v4 per user-initiated action and retry on network errors using the same key.

PDF & CSV output
- The payslip PDF lists employee name, role, department, CNP, working days, vacation days, bonuses total and details, and the computed salary.
- Aggregated CSVs contain a row per employee with bonuses metadata (count, total) and salaries.

Developer notes
- Logging: structured logging to `logs/requests.log` and `logs/send.log` using a JSON-per-line format. Request middleware resolves the acting user and sets `owner_id` for idempotency and audit.
- If you change models, add migrations: `python manage.py makemigrations` then `python manage.py migrate`.

Troubleshooting
- If you don't see bonuses in generated artifacts, ensure the bonus `date` is in the target year/month (current month is used by generation endpoints when no explicit period is provided).
- Check `logs/requests.log` and `logs/send.log` for structured entries that include the `actor_id` and `target_employee_id` to debug who triggered a send



