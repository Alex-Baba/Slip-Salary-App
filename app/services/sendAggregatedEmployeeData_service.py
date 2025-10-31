from django.core.exceptions import ValidationError
from app.services.email_provider_service import send_email
from .email_templates import build_aggregate_subject, build_aggregate_bodies
from datetime import datetime
from django.test import RequestFactory
from django.urls import reverse
from io import StringIO
import csv

from app.db.models import Employee
from app.api.routers.aggregateEmployeeData import AggregateEmployeeDataView

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

def send_aggregated_csv_email(employee_id: int, year: int | None = None, month: int | None = None) -> dict:
	"""Fetch aggregated data, build CSV, and email via provider chain."""
	aggregated = fetch_aggregated_employee_data(employee_id, year, month)
	try:
		employee = Employee.objects.get(id=employee_id)
	except Employee.DoesNotExist:
		raise ValidationError({"employee_id": "Employee not found"})
	csv_bytes = generate_employee_csv(aggregated)
	period_ref = datetime.utcnow()
	subject = build_aggregate_subject(period_ref)
	bodies = build_aggregate_bodies(employee.first_name, aggregated.get('bonuses', []))
	resp = send_email(
		to=[employee.email],
		subject=subject,
		text=bodies["text"],
		html=bodies["html"],
		attachments=[(f"employee_{employee_id}_aggregate.csv", csv_bytes, "text/csv")]
	)
	resp["employee_id"] = employee_id
	resp["rows"] = 2
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
	"""Collect all direct subordinates for manager and send consolidated CSV to manager (or override recipient)."""
	try:
		manager = Employee.objects.get(id=manager_id)
	except Employee.DoesNotExist:
		raise ValidationError({"manager_id": "Manager not found"})
	subs = Employee.objects.filter(manager_id=manager_id).order_by('id')
	if not subs.exists():
		return {"manager_id": manager_id, "sent": False, "error": "No subordinates"}
	rows = []
	for emp in subs:
		rows.append(fetch_aggregated_employee_data(emp.id, year, month))
	csv_bytes = generate_manager_csv(rows)
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
		attachments=[(f"manager_{manager_id}_team_aggregate.csv", csv_bytes, "text/csv")]
	)
	resp["manager_id"] = manager_id
	resp["employee_count"] = subs.count()
	return resp

__all__ = ["fetch_aggregated_employee_data", "generate_employee_csv", "send_aggregated_csv_email", "generate_manager_csv", "send_manager_aggregated_csv_email"]
