from django.core.exceptions import ValidationError
from app.services.email_provider_service import send_email
from .email_templates import build_payslip_subject, build_payslip_bodies
from datetime import datetime
import os, hashlib, time, io
import pyzipper
from app.db.models import Employee
from app.services.createPdfForEmployees_service import get_payslip_filepath
from app.services.archive_service import archive_bytes
import os
import logging
import json

logger = logging.getLogger('send')


def fetch_payslip_pdf(employee_id: int) -> bytes:
	"""Read the persisted payslip PDF for the current month.

	Raises ValidationError if the file doesn't exist or the employee is missing.
	"""
	try:
		Employee.objects.get(id=employee_id)
	except Employee.DoesNotExist:
		raise ValidationError({"employee_id": "Employee not found"})
	path = get_payslip_filepath(employee_id)
	if not os.path.exists(path):
		raise ValidationError({"pdf": "Payslip not found. Generate it first using ?generate=1 on the create_pdf endpoint."})
	with open(path, 'rb') as fh:
		return fh.read()

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
		# Archive the sent zip for audit purposes
		try:
			y = period_ref.year
			m = period_ref.month
			archive_path = archive_bytes(zip_bytes, 'payslips', y, m, f"employee_{employee_id}_payslip.zip", {
				'employee_id': employee_id,
				'recipient': employee.email,
				'provider_response': resp,
			})
			resp['archive_path'] = archive_path
			info = {'employee_id': employee_id, 'recipient': employee.email, 'provider_response': resp, 'archive_path': archive_path}
			logger.info('payslip_sent %s', json.dumps(info, default=str))
			# Remove the original PDF now that we've archived the zipped copy.
			try:
				original_path = get_payslip_filepath(employee_id)
				if os.path.exists(original_path):
					os.remove(original_path)
					resp['deleted_original'] = True
					logger.info('payslip_original_deleted %s', json.dumps({'employee_id': employee_id, 'path': original_path}, default=str))
				else:
					resp['deleted_original'] = False
					logger.warning('payslip_original_missing %s', json.dumps({'employee_id': employee_id, 'path': original_path}, default=str))
			except Exception as ex_del:
				resp['deleted_original_error'] = str(ex_del)
				logger.warning('payslip_original_delete_failed %s', json.dumps({'employee_id': employee_id, 'error': str(ex_del)}, default=str))
		except Exception as ex:
			resp['archive_error'] = str(ex)
			warn = {'employee_id': employee_id, 'recipient': employee.email, 'error': str(ex)}
			logger.warning('payslip_archive_failed %s', json.dumps(warn, default=str))
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
		# Archive the sent zip for audit purposes
		try:
			y = period_ref.year
			m = period_ref.month
			archive_path = archive_bytes(zip_bytes, 'payslips', y, m, f"employee_{employee_id}_payslip.zip", {
				'employee_id': employee_id,
				'recipient': employee.email,
				'provider_response': resp,
			})
			resp['archive_path'] = archive_path
			info = {'employee_id': employee_id, 'recipient': employee.email, 'provider_response': resp, 'archive_path': archive_path}
			logger.info('payslip_sent %s', json.dumps(info, default=str))
		except Exception as ex:
			resp['archive_error'] = str(ex)
			warn = {'employee_id': employee_id, 'recipient': employee.email, 'error': str(ex)}
			logger.warning('payslip_archive_failed %s', json.dumps(warn, default=str))
	resp["employee_id"] = employee_id
	return resp

__all__ = ["fetch_payslip_pdf", "send_payslip_email"]


