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

Note: after adding a new `RevokedToken` model (used to revoke JWTs on logout) run Django migrations locally and in your deployment:

	python manage.py makemigrations
	python manage.py migrate

This will create the table used to store revoked tokens so the `/api/auth/logout/` endpoint works correctly.
- Extend email flows (multi-employee batch sending, HTML templates).

## Email Sending (SendGrid Priority)

Email provider priority chain: SendGrid > Django SMTP backend.

If `SENDGRID_API_KEY` is set, emails (payslip PDFs and aggregated CSV reports) are sent via SendGrid. If absent or SendGrid fails, we fall back to Django's configured SMTP backend.

Environment variables:
```
SENDGRID_API_KEY=SG.xxxxxx_actual_api_key
SENDGRID_FROM_EMAIL=payroll@yourdomain.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.yourprovider.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_smtp_user
EMAIL_HOST_PASSWORD=your_smtp_password_or_app_password
EMAIL_USE_TLS=1
DEFAULT_FROM_EMAIL=payroll@yourdomain.com
```

Setup notes:
- For Gmail, use an App Password (2FA required) for `EMAIL_HOST_PASSWORD`.
- For higher deliverability, set SPF/DKIM records on your domain (SendGrid documentation provides DNS entries).
- Attachments are sent as standard MIME attachments (PDF for payslips, CSV for aggregated data).

Fallback behavior:
- If SendGrid is not configured or returns a non-success status, the system automatically attempts Django SMTP.

Extensibility:
- The provider abstraction (`email_provider_service.py`) allows adding more providers later with minimal changes.


## Notes

This is an early integration of the frontend; PDF/CSV email endpoints exist but not yet wired into the UI.

