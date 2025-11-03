from django.core.exceptions import ValidationError
from app.services.email_provider_service import send_email
from .email_templates import build_payslip_subject, build_payslip_bodies
from datetime import datetime
import os, hashlib, time, io
import pyzipper
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
	# Validate CNP for password use.
	cnp = (employee.cnp or '').strip()
	if len(cnp) != 13 or not cnp.isdigit():
		from django.core.exceptions import ValidationError
		raise ValidationError({"cnp": "Invalid CNP (must be 13 digits) for encrypted archive"})
	period_ref = datetime.utcnow()
	if neutral_mode:
		# Generic subject & body, rename attachment to avoid payroll keywords.
		# Add a short token to reduce similarity across messages.
		token_source = f"{employee_id}-{int(time.time())}".encode()
		short_hash = hashlib.sha256(token_source).hexdigest()[:8]
		subject = f"Document for Review - Ref #{employee_id}-{short_hash}"
		# Use the same body builders as the non-neutral path to keep wording
		# centralized in app/services/email_templates.py
		bodies = build_payslip_bodies(employee.first_name)
		text_body = bodies.get('text', '')
		html_body = bodies.get('html', '')
		attachment_name = f"document_{employee_id}.zip"
		zip_buffer = io.BytesIO()
		with pyzipper.AESZipFile(zip_buffer, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
			zf.setpassword(cnp.encode())
			zf.writestr(f"payslip_{employee_id}.pdf", pdf_bytes)
		zip_bytes = zip_buffer.getvalue()
		text_body += "\nArchive password: your CNP (13 digits)."
		html_body += "<p style='font-size:12px;color:#666'>Archive password: your CNP (13 digits).</p>"
		resp = send_email(
			to=[employee.email],
			subject=subject,
			text=text_body,
			html=html_body,
			attachments=[(attachment_name, zip_bytes, "application/zip")]
		)
	else:
		subject = build_payslip_subject(period_ref)
		bodies = build_payslip_bodies(employee.first_name)
		attachment_name = f"payslip_{employee_id}.zip"
		zip_buffer = io.BytesIO()
		with pyzipper.AESZipFile(zip_buffer, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
			zf.setpassword(cnp.encode())
			zf.writestr(f"payslip_{employee_id}.pdf", pdf_bytes)
		zip_bytes = zip_buffer.getvalue()
		bodies["text"] += "\nArchive password: your CNP (13 digits)."
		bodies["html"] += "<p style='font-size:12px;color:#666'>Archive password: your CNP (13 digits).</p>"
		resp = send_email(
			to=[employee.email],
			subject=subject,
			text=bodies["text"],
			html=bodies["html"],
			attachments=[(attachment_name, zip_bytes, "application/zip")]
		)
	resp["employee_id"] = employee_id
	return resp

__all__ = ["fetch_payslip_pdf", "send_payslip_email"]


