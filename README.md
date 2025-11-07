# Proiect Payroll System
This repository contains a small payroll web application (Django + DRF backend, Vite + React frontend) used for generating and sending monthly payslips and aggregated CSV reports. It supports bonuses, attendance-based prorated salary calculations, idempotent actions (Idempotency-Key), and structured request logging.

## Quick summary
- Backend: Django (DRF) with services organized under `app/services` and routers under `app/api/routers`.
- Frontend: Vite + React in `frontend/` with simple admin dashboard at `frontend/src/pages/Dashboard.tsx`.
- Persistence: PostgreSQL expected in production (Docker compose used during development/testing).

## Getting started (development)
These are minimal steps to get the project running locally for development. Adjust environment variables as needed.

# Slip Salary App — Detailed README

This file documents how to run, develop, and use the Slip Salary payroll app (Django backend + React frontend). It includes setup instructions, common endpoints with examples, idempotency guidance, RBAC rules, logging, and troubleshooting.

Table of contents
- About
- Quick start (development)
	- Prerequisites
	- Backend setup
	- Frontend setup
	- Optional: Docker compose
- Project layout
- Endpoints & examples
	- Authentication
	- Employee / payslip (PDF)
	- Aggregated CSV (create/send)
	- Manager / batch endpoints
	- Bonus management
- Idempotency and client guidance
- RBAC and permissions
- Logging & audit
- Troubleshooting
- Tests & contributing

---

About

Slip Salary provides a lightweight payroll stack used to:
- Generate per-employee payslip PDFs
- Generate aggregated employee CSVs (per employee & per manager/team)
- Send payslips and aggregates via email
- Track bonuses and attendance

Quick start (development)

Prerequisites
- Python 3.11+
- Node 16+
- PostgreSQL for realistic development (sqlite may be used for quick testing)
- Docker & Docker Compose (optional, recommended for parity)

Backend setup

1) Create & activate a virtual environment

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2) Install Python requirements

```powershell
pip install -r rquirements.txt
```

3) Environment

Copy `.env.example` to `.env` (if present) and set at least these values:

```
DJANGO_SECRET_KEY=change_me
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1
JWT_SECRET=change_me_jwt
JWT_EXP_MINUTES=60
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

4) Migrate & create superuser

```powershell
python manage.py migrate
python manage.py createsuperuser
```

5) Run backend

```powershell
python manage.py runserver
```

Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

Optional: Docker compose

If you want containers, create/adjust `docker-compose.yml` (web + db). Example commands:

```powershell
docker compose build
docker compose up
```

Project layout

- `app/` - Django app
	- `api/routers/` - DRF endpoints
	- `services/` - business logic (PDF/CSV generation, salary computation, idempotency, email providers)
	- `db/models/` - Django models
	- `middleware/` - request logging middleware
- `frontend/` - Vite + React
- `media/` - generated artifacts (payslips, aggregates)
- `logs/` - structured JSON logs

Endpoints & examples

Authentication

- POST `/api/auth/login/`
	- Body: {"email": "user@example.com", "password": "secret"}
	- Response: {"token": "<jwt>", "user_id": 1}

Example (curl):

```bash
curl -X POST "http://localhost:8000/api/auth/login/" \
	-H "Content-Type: application/json" \
	-d '{"email":"admin@example.com","password":"secret"}'
```

Employee / payslip (PDF)

- POST `/api/employees/<id>/generate_pdf/` — generate & save PDF (Idempotency-Key supported)
- POST `/api/employees/<id>/send_payslip/` — send the payslip via email (Idempotency-Key supported)

Example generate PDF (curl):

```bash
curl -X POST "http://localhost:8000/api/employees/42/generate_pdf/" \
	-H "Authorization: Bearer <token>" \
	-H "Idempotency-Key: $(uuidgen)"
```

Aggregated CSV (create/send)

- POST `/api/employees/<id>/generate_aggregate/` — generate & save CSV for employee `<id>` for specified `year`/`month` (defaults to current month)
- POST `/api/employees/<id>/send_aggregated_csv/` — send the generated CSV by email

Manager / batch endpoints (important)

These are the manager/team oriented endpoints you asked to highlight:

- POST `/api/employees/create_aggregated_employee_data/` (or `/createAggregatedEmployeeData`) — generates employee Excel/CSV for a period (saved to `media/aggregates/<year>-<month>/`).
- POST `/api/employees/send_aggregated_employee_data/` (or `/sendAggregatedEmployeeData`) — sends the generated CSV via email and archives it.
- POST `/api/employees/create_pdf_for_employees/` (or `/createPdfForEmployees`) — generates and saves PDF payslips for an employee for the period.
- POST `/api/employees/send_pdf_to_employees/` (or `/sendPdfToEmployees`) — sends generated PDF payslips to employees; supports `Idempotency-Key`.

Note: exact path strings live in `app/api/routers/`; the frontend client (`frontend/src/api/client.ts`) contains wrappers you can reuse.

Bonus management

- POST `/api/bonuses/create/` — body: { employee_id, amount, description, date }
- GET `/api/bonuses/list/?employee_id=<id>` — list bonuses (scoped per RBAC)

Idempotency and client guidance

Use `Idempotency-Key` for any potentially repeated user action that would create a persistent side-effect (sends, generations). Recommendations:
- Generate a UUID v4 per user-facing action and include it in the `Idempotency-Key` header.
- Retry network errors using the same key — backend will return the cached response or indicate conflict.
- Keys are owner-scoped; a key used by alice cannot be used by bob to retrieve alice's result.

RBAC and permissions

- Admin: full access
- Manager: can act only on direct reports (i.e., `target.manager_id == actor.id`)
- Employee: can act on themselves

Logging & audit

Requests and send actions are logged in structured JSON files under `logs/`:
- `logs/requests.log` — request-level structured logs with `actor_id` and `owner_id` filled by middleware
- `logs/send.log` — records of send/archive actions

Common troubleshooting

- Bonus not appearing in generated output: verify the bonus `date` is in the target period. Generation defaults to the current month when no `year`/`month` are provided.
- Forbidden/403: check that the actor actually manages the target employee (direct-report rule). Admins bypass this restriction.
- Missing PDFs/CSVs: check `media/payslips/` and `media/aggregates/` for saved files and `logs/send.log` for archive/send details.

Tests & contributing

- Run tests (project-specific): `python manage.py test` or `pytest` if configured.
- Lint and formatting: follow project conventions.

Next steps I can take for you

- Create `docs/IDEMPOTENCY.md` with concrete client examples (curl, JS, Python) and best practices.
- Add example `curl` snippets for the manager endpoints including `Idempotency-Key` usage.
- Provide a `docker-compose.yml` example to run Postgres + backend + frontend locally.

---

If you want any of the next steps implemented, tell me which one and I will add it.



