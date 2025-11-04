from django.core.exceptions import ValidationError
from app.services.email_provider_service import send_email
from .email_templates import build_aggregate_subject, build_aggregate_bodies
from datetime import datetime
from io import StringIO
import csv
import os
from django.conf import settings

from app.db.models import Employee
from app.services.aggregateEmployeeData_service import generate_aggregate_employee_report
from app.services.archive_service import archive_bytes
from io import BytesIO
import zipfile
import logging
import json

logger = logging.getLogger('send')

AGGREGATE_ENDPOINT_NAME = 'aggregate-employee-data'

def fetch_aggregated_employee_data(employee_id: int, year: int | None = None, month: int | None = None) -> dict:
	"""Call existing aggregate endpoint internally to avoid duplicating logic."""
	try:
		Employee.objects.get(id=employee_id)
	except Employee.DoesNotExist:
		raise ValidationError({"employee_id": "Employee not found"})
	# Call the aggregation service directly to avoid an import cycle with routers
	try:
		data = generate_aggregate_employee_report(employee_id=employee_id, year=year, month=month)
		return data
	except Exception as e:
		# Map service exceptions to ValidationError for callers
		raise ValidationError({"aggregate": f"Failed to fetch aggregation: {str(e)}"})

def generate_employee_csv(aggregated: dict) -> bytes:
	"""Generate a CSV representation of aggregated employee data."""
	output = StringIO()
	writer = csv.writer(output)
	# Header
	writer.writerow([
		'first_name','last_name','email','role','department','manager',
		'working_days','leave_days','bonuses_count','total_bonus','salary','total_salary'
	])
	att = aggregated.get('attendance', {})
	bonuses = aggregated.get('bonuses', [])
	writer.writerow([
		aggregated.get('first_name'),
		aggregated.get('last_name'),
		aggregated.get('email'),
		aggregated.get('role'),
		aggregated.get('department'),
		aggregated.get('manager'),
		att.get('working_days', 0),
		att.get('leave_days', 0),
		len(bonuses),
		aggregated.get('total_bonus', 0),
		aggregated.get('salary'),
		aggregated.get('total_salary'),
	])
	return output.getvalue().encode('utf-8')


def _aggregate_dir_for(year: int, month: int) -> str:
	base = getattr(settings, 'MEDIA_ROOT', None) or os.path.join(settings.BASE_DIR, 'media')
	path = os.path.join(base, 'aggregates', f"{year}-{month:02d}")
	return path


def get_aggregate_filepath(employee_id: int, year: int | None = None, month: int | None = None) -> str:
	now = datetime.today()
	y = year or now.year
	m = month or now.month
	directory = _aggregate_dir_for(y, m)
	filename = f"employee_{employee_id}_aggregate.csv"
	return os.path.join(directory, filename)


def save_aggregate_csv(employee_id: int, csv_bytes: bytes, year: int | None = None, month: int | None = None) -> str:
	path = get_aggregate_filepath(employee_id, year, month)
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, 'wb') as fh:
		fh.write(csv_bytes)
	return path


def fetch_aggregate_csv(employee_id: int, year: int | None = None, month: int | None = None) -> bytes:
	# respect environment MEDIA_ROOT for tests using monkeypatch.setenv
	base = os.getenv('MEDIA_ROOT') or getattr(settings, 'MEDIA_ROOT', None) or os.path.join(settings.BASE_DIR, 'media')
	now = datetime.today()
	y = year or now.year
	m = month or now.month
	directory = os.path.join(base, 'aggregates', f"{y}-{m:02d}")
	filename = f"employee_{employee_id}_aggregate.csv"
	path = os.path.join(directory, filename)
	if not os.path.exists(path):
		raise ValidationError({"csv": "Aggregated CSV not found. Generate it first using the generate endpoint."})
	with open(path, 'rb') as fh:
		return fh.read()

def send_aggregated_csv_email(employee_id: int, year: int | None = None, month: int | None = None) -> dict:
	"""Send an already-generated aggregated CSV for an employee.

	The CSV must be generated and saved beforehand using the generate endpoint. This avoids
	regenerating and ensures admins/managers explicitly create the artifact.
	"""
	try:
		employee = Employee.objects.get(id=employee_id)
	except Employee.DoesNotExist:
		raise ValidationError({"employee_id": "Employee not found"})
	# Read persisted CSV (raises ValidationError if missing)
	csv_bytes = fetch_aggregate_csv(employee_id, year, month)
	period_ref = datetime.utcnow()
	subject = build_aggregate_subject(period_ref)
	bodies = build_aggregate_bodies(employee.first_name, [])
	resp = send_email(
		to=[employee.email],
		subject=subject,
		text=bodies["text"],
		html=bodies["html"],
		attachments=[(f"employee_{employee_id}_aggregate.csv", csv_bytes, "text/csv")]
	)
	# Archive the CSV for audit (store as ZIP, no password)
	try:
		now = datetime.today()
		y = year or now.year
		m = month or now.month
		# create in-memory zip containing the CSV
		zip_buffer = BytesIO()
		with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
			zf.writestr(f"employee_{employee_id}_aggregate.csv", csv_bytes)
		zip_bytes = zip_buffer.getvalue()
		archive_path = archive_bytes(zip_bytes, 'aggregates', y, m, f"employee_{employee_id}_aggregate.zip", {
			'employee_id': employee_id,
			'recipient': employee.email,
			'provider_response': resp,
		})
		resp['archive_path'] = archive_path
		info = {'employee_id': employee_id, 'recipient': employee.email, 'provider_response': resp, 'archive_path': archive_path}
		logger.info('aggregate_sent %s', json.dumps(info, default=str))
		# Remove the original generated CSV now that it's archived as a ZIP
		try:
			orig_path = get_aggregate_filepath(employee_id, y, m)
			if os.path.exists(orig_path):
				os.remove(orig_path)
				resp['deleted_original'] = True
				logger.info('aggregate_original_deleted %s', json.dumps({'employee_id': employee_id, 'path': orig_path}, default=str))
			else:
				resp['deleted_original'] = False
				logger.warning('aggregate_original_missing %s', json.dumps({'employee_id': employee_id, 'path': orig_path}, default=str))
		except Exception as ex_del:
			resp['deleted_original_error'] = str(ex_del)
			logger.warning('aggregate_original_delete_failed %s', json.dumps({'employee_id': employee_id, 'error': str(ex_del)}, default=str))
	except Exception as ex:
		resp['archive_error'] = str(ex)
		warn = {'employee_id': employee_id, 'recipient': employee.email, 'error': str(ex)}
		logger.warning('aggregate_archive_failed %s', json.dumps(warn, default=str))
	resp["employee_id"] = employee_id
	return resp

def generate_manager_csv(rows: list[dict]) -> bytes:
	"""Generate CSV for multiple employees under a manager."""
	output = StringIO()
	writer = csv.writer(output)
	writer.writerow([
		'first_name','last_name','email','role','department','manager','working_days','leave_days','bonuses_count','total_bonus','salary','total_salary'
	])
	for aggregated in rows:
		att = aggregated.get('attendance', {})
		bonuses = aggregated.get('bonuses', [])
		writer.writerow([
			aggregated.get('first_name'),
			aggregated.get('last_name'),
			aggregated.get('email'),
			aggregated.get('role'),
			aggregated.get('department'),
			aggregated.get('manager'),
			att.get('working_days', 0),
			att.get('leave_days', 0),
			len(bonuses),
			aggregated.get('total_bonus', 0),
			aggregated.get('salary'),
			aggregated.get('total_salary'),
		])
	return output.getvalue().encode('utf-8')

def send_manager_aggregated_csv_email(manager_id: int, year: int | None = None, month: int | None = None, to_email: str | None = None) -> dict:
	"""Send an already-generated team aggregate CSV for the manager.

	Requires that a manager-team CSV has been generated and saved previously.
	"""
	try:
		manager = Employee.objects.get(id=manager_id)
	except Employee.DoesNotExist:
		raise ValidationError({"manager_id": "Manager not found"})
	# Manager team file path convention
	now = datetime.today()
	y = year or now.year
	m = month or now.month
	base = os.getenv('MEDIA_ROOT') or getattr(settings, 'MEDIA_ROOT', None) or os.path.join(settings.BASE_DIR, 'media')
	dirpath = os.path.join(base, 'aggregates', f"{y}-{m:02d}")
	filename = f"manager_{manager_id}_team_aggregate.csv"
	path = os.path.join(dirpath, filename)
	if not os.path.exists(path):
		raise ValidationError({"csv": "Manager aggregate CSV not found. Generate it first using the generate endpoint."})
	with open(path, 'rb') as fh:
		csv_bytes = fh.read()
	period_ref = datetime.utcnow()
	subject = f"Team Compensation Summary - {period_ref.strftime('%B %Y')}"
	bodies = build_aggregate_bodies(manager.first_name, [])  # summary text reused
	bodies['text'] = bodies['text'].replace('Your monthly', 'Team monthly')
	bodies['html'] = bodies['html'].replace('Your monthly', 'Team monthly')
	recipient = to_email or manager.email
	resp = send_email(
		to=[recipient],
		subject=subject,
		text=bodies["text"],
		html=bodies["html"],
		attachments=[(filename, csv_bytes, "text/csv")]
	)
	# Archive the manager CSV for audit (store as ZIP, no password)
	try:
		now = datetime.today()
		y = year or now.year
		m = month or now.month
		zip_buffer = BytesIO()
		with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
			zf.writestr(filename, csv_bytes)
		zip_bytes = zip_buffer.getvalue()
		archive_path = archive_bytes(zip_bytes, 'aggregates', y, m, filename.replace('.csv', '.zip'), {
			'manager_id': manager_id,
			'recipient': recipient,
			'provider_response': resp,
		})
		resp['archive_path'] = archive_path
		info = {'manager_id': manager_id, 'recipient': recipient, 'provider_response': resp, 'archive_path': archive_path}
		logger.info('manager_aggregate_sent %s', json.dumps(info, default=str))
		# Remove the original manager CSV now that we've archived the zipped copy.
		try:
			if os.path.exists(path):
				os.remove(path)
				resp['deleted_original'] = True
				logger.info('manager_aggregate_original_deleted %s', json.dumps({'manager_id': manager_id, 'path': path}, default=str))
			else:
				resp['deleted_original'] = False
				logger.warning('manager_aggregate_original_missing %s', json.dumps({'manager_id': manager_id, 'path': path}, default=str))
		except Exception as ex_del:
			resp['deleted_original_error'] = str(ex_del)
			logger.warning('manager_aggregate_original_delete_failed %s', json.dumps({'manager_id': manager_id, 'error': str(ex_del)}, default=str))
	except Exception as ex:
		resp['archive_error'] = str(ex)
		warn = {'manager_id': manager_id, 'recipient': recipient, 'error': str(ex)}
		logger.warning('manager_aggregate_archive_failed %s', json.dumps(warn, default=str))
	resp["manager_id"] = manager_id
	return resp

__all__ = ["fetch_aggregated_employee_data", "generate_employee_csv", "send_aggregated_csv_email", "generate_manager_csv", "send_manager_aggregated_csv_email"]
