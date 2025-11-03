from django.core.exceptions import ValidationError
from app.services.email_provider_service import send_email
from .email_templates import build_aggregate_subject, build_aggregate_bodies
from datetime import datetime
from django.test import RequestFactory
from django.urls import reverse
from io import StringIO
import csv
import os
from django.conf import settings

from app.db.models import Employee
from app.api.routers.aggregateEmployeeData import AggregateEmployeeDataView
from app.services.archive_service import archive_bytes
from io import BytesIO
import zipfile

AGGREGATE_ENDPOINT_NAME = 'aggregate-employee-data'

def fetch_aggregated_employee_data(employee_id: int, year: int | None = None, month: int | None = None) -> dict:
	"""Call existing aggregate endpoint internally to avoid duplicating logic."""
	try:
		Employee.objects.get(id=employee_id)
	except Employee.DoesNotExist:
		raise ValidationError({"employee_id": "Employee not found"})
	factory = RequestFactory()
	params = {}
	if year is not None:
		params['year'] = str(year)
	if month is not None:
		params['month'] = str(month)
	params['employee_id'] = str(employee_id)
	query = '?' + '&'.join(f"{k}={v}" for k,v in params.items())
	path = reverse(AGGREGATE_ENDPOINT_NAME) + query
	request = factory.get(path)
	response = AggregateEmployeeDataView.as_view()(request)
	if response.status_code != 200:
		raise ValidationError({"aggregate": f"Failed to fetch aggregation: status {response.status_code}"})
	return response.data

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
	path = get_aggregate_filepath(employee_id, year, month)
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
	except Exception as ex:
		resp['archive_error'] = str(ex)
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
	base = getattr(settings, 'MEDIA_ROOT', None) or os.path.join(settings.BASE_DIR, 'media')
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
	except Exception as ex:
		resp['archive_error'] = str(ex)
	resp["manager_id"] = manager_id
	return resp

__all__ = ["fetch_aggregated_employee_data", "generate_employee_csv", "send_aggregated_csv_email", "generate_manager_csv", "send_manager_aggregated_csv_email"]
