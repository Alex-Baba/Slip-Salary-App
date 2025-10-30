# Proiect Payroll System

Backend: Django + PostgreSQL (Docker) providing employee management, attendance, salary aggregation, bonuses, payslip PDF & CSV emailing, and JWT authentication.

Frontend: React (Vite + TypeScript) starting with a login page consuming the JWT auth endpoint.

## Backend Setup

1. Copy `.env.example` (if present) to `.env` or create `.env` with at least:
```
DJANGO_SECRET_KEY=change_me
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1
JWT_SECRET=change_me_jwt
JWT_EXP_MINUTES=60
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```
For production add DB credentials and real email settings.

2. Build & start services (adjust path if needed):
Use Docker compose (ensure a service for web and db exists; not shown here). If not yet created, you can run `docker build -t proiect-backend .` then `docker run -p 8000:8000 proiect-backend`.

3. Apply migrations:
`python manage.py migrate`

4. Create a superuser (optional for admin):
`python manage.py createsuperuser`

5. Run development server:
`python manage.py runserver 0.0.0.0:8000`

## Authentication

Endpoint: `POST /api/auth/login/` with JSON body:
```
{"email": "user@example.com", "password": "plain_or_hashed"}
```
Returns:
```
{"token": "<jwt>", "user_id": 1}
```
Store token client side (localStorage) and send `Authorization: Bearer <token>` for protected future endpoints.

## CORS

Configured to allow origin `http://localhost:5173` (Vite dev). Override via env `FRONTEND_ORIGIN`.

## Frontend Setup

1. Navigate to `frontend/`
2. Copy `.env.example` to `.env` if you need to override API base (default `http://localhost:8000`).
3. Install dependencies:
`npm install`
4. Start dev server:
`npm run dev`

Visit http://localhost:5173 to view the login page.

## Frontend Structure

`src/pages/Login.tsx` - Login form calling backend.
`src/components/ProtectedRoute.tsx` - Simple auth guard.
`src/pages/Dashboard.tsx` - Placeholder secured page.
`src/api/client.ts` - Fetch helpers.

## Next Steps

- Implement token verification & protected backend endpoints.
- Add employee/attendance management UI.
- Improve styling (Tailwind or component library).
- Add logout & refresh token flow.
- Extend email flows (multi-employee batch sending, HTML templates).

## Mailgun Email Sending

If `MAILGUN_API_KEY` and `MAILGUN_DOMAIN` are set in `.env`, payslip emails will be sent via Mailgun's HTTP API instead of the Django email backend.

Environment variables required:
```
MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
MAILGUN_DOMAIN=sandboxXXXXXX.mailgun.org   # or your verified domain
MAILGUN_BASE_URL=https://api.mailgun.net/v3
DEFAULT_FROM_EMAIL=payroll@yourdomain.com  # used as 'from' when available
```

Sandbox notes:
- Mailgun sandbox domains only deliver to approved/verified recipient addresses.
- Add your recipient email in Mailgun dashboard under Authorized Recipients.
- The service attaches the PDF payslip as `payslip_<employee_id>.pdf`.

Production domain:
- Verify your domain DNS (TXT + MX + SPF + DKIM records) per Mailgun instructions.
- Replace sandbox domain with your domain (e.g. `mg.yourdomain.com`).
- Ensure `DEFAULT_FROM_EMAIL` matches a permitted sender (e.g. `payroll@yourdomain.com`).

Fallback behavior:
- If Mailgun variables are missing, the system falls back to Django's configured `EMAIL_BACKEND` (console by default for dev).


## Notes

This is an early integration of the frontend; PDF/CSV email endpoints exist but not yet wired into the UI.

