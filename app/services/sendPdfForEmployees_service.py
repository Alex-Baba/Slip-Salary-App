from django.core.exceptions import ValidationError
from app.services.email_provider_service import send_email
from .email_templates import build_payslip_subject, build_payslip_bodies
from datetime import datetime
import os, hashlib, time
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
	"""Fetch existing payslip PDF and send via provider chain (SendGrid -> Django SMTP)."""
	try:
		employee = Employee.objects.get(id=employee_id)
	except Employee.DoesNotExist:
		raise ValidationError({"employee_id": "Employee not found"})
	neutral_mode = os.getenv('NEUTRAL_EMAIL_MODE') in ('1','true','True')
	pdf_bytes = fetch_payslip_pdf(employee_id)
	period_ref = datetime.utcnow()
	if neutral_mode:
		# Generic subject & body, rename attachment to avoid payroll keywords.
		# Add a short token to reduce similarity across messages.
		token_source = f"{employee_id}-{int(time.time())}".encode()
		short_hash = hashlib.sha256(token_source).hexdigest()[:8]
		subject = f"Document for Review - Ref #{employee_id}-{short_hash}"
		text_body = (
			f"Hello {employee.first_name},\n\n"
			"Your requested document is attached. Please review and retain for your records.\n\n"
			"--\nAutomated Notification"
		)
		html_body = (
			f"<p>Hi {employee.first_name},</p>"
			"<p>Your requested document is attached. Please review and retain for your records.</p>"
			"<p style='font-size:12px;color:#666'>Automated Notification</p>"
		)
		attachment_name = f"document_{employee_id}.pdf"
		resp = send_email(
			to=[employee.email],
			subject=subject,
			text=text_body,
			html=html_body,
			attachments=[(attachment_name, pdf_bytes, "application/pdf")]
		)
	else:
		subject = build_payslip_subject(period_ref)
		bodies = build_payslip_bodies(employee.first_name)
		resp = send_email(
			to=[employee.email],
			subject=subject,
			text=bodies["text"],
			html=bodies["html"],
			attachments=[(f"payslip_{employee_id}.pdf", pdf_bytes, "application/pdf")]
		)
	resp["employee_id"] = employee_id
	return resp

__all__ = ["fetch_payslip_pdf", "send_payslip_email"]


