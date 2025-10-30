from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
import os
from app.services.mailgun_service import mailgun_available, send_mailgun_message
from django.test import RequestFactory
from django.urls import reverse
from app.db.models import Employee
from app.api.routers.createPdfEmployees import CreatePdfEmployeesView

def fetch_payslip_pdf(employee_id: int) -> bytes:
	"""Call the existing create_pdf endpoint internally to obtain the PDF bytes."""
	try:
		Employee.objects.get(id=employee_id)
	except Employee.DoesNotExist:
		raise ValidationError({"employee_id": "Employee not found"})
	factory = RequestFactory()
	path = reverse('create-pdf-employees') + f"?employee_id={employee_id}"
	request = factory.get(path)
	response = CreatePdfEmployeesView.as_view()(request)
	if response.status_code != 200:
		raise ValidationError({"pdf": f"Failed to generate PDF: status {response.status_code}"})
	return response.content

def send_payslip_email(employee_id: int) -> dict:
	"""Fetch existing payslip PDF and send via Mailgun if configured else Django Email backend."""
	try:
		employee = Employee.objects.get(id=employee_id)
	except Employee.DoesNotExist:
		raise ValidationError({"employee_id": "Employee not found"})
	pdf_bytes = fetch_payslip_pdf(employee_id)
	subject = "Your Monthly Payslip"
	text_body = f"Hello {employee.first_name},\n\nPlease find attached your payslip.\n\nRegards, Payroll"

	if mailgun_available():
		from_email = os.getenv('DEFAULT_FROM_EMAIL', f'postmaster@{os.getenv("MAILGUN_DOMAIN", "example.com")}')
		mg_resp = send_mailgun_message(
			to=[employee.email],
			subject=subject,
			text=text_body,
			attachments=[(f"payslip_{employee_id}.pdf", pdf_bytes, "application/pdf")]
		)
		mg_resp["employee_id"] = employee_id
		mg_resp["via"] = "mailgun"
		return mg_resp

	# Fallback to Django email backend
	email = EmailMessage(subject=subject, body=text_body, to=[employee.email])
	email.attach(filename=f"payslip_{employee_id}.pdf", content=pdf_bytes, mimetype="application/pdf")
	sent = email.send(fail_silently=False)
	return {"sent": bool(sent), "employee_id": employee_id, "via": "django-backend"}

__all__ = ["fetch_payslip_pdf", "send_payslip_email"]


