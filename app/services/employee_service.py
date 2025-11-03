from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from app.db.models import Employee, EmployeeRole, Department, Attendance
from app.api.schemas import EmployeeCreateSchema, EmployeeSchema, EmployeeRoleSchema, EmployeeUpdateSchema

ROLE_BASE_SALARIES = {
	"employee": 2500.0,
	"manager": 4000.0,
	"admin": 5000.0,
}


def create_employee(data: EmployeeCreateSchema) -> Employee:
	"""Create an Employee from validated pydantic data."""
	try:
		role = EmployeeRole.objects.get(id=data.role_id)
	except EmployeeRole.DoesNotExist:
		raise ValidationError({"role_id": "Invalid role id"})

	# Pre-check uniqueness to provide clearer error messages
	if Employee.objects.filter(email=data.email).exists():
		raise ValidationError({"email": "Email already in use"})
	if Employee.objects.filter(cnp=data.cnp).exists():
		raise ValidationError({"cnp": "CNP already in use"})

	manager = None
	if data.manager_id is not None:
		try:
			manager = Employee.objects.get(id=data.manager_id)
		except Employee.DoesNotExist:
			raise ValidationError({"manager_id": "Invalid manager id"})
		if manager.role.role not in ("manager", "admin"):
			raise ValidationError({"manager_id": "Selected employee is not a manager"})

	department = None
	if getattr(data, 'department_id', None) is not None:
		try:
			department = Department.objects.get(id=data.department_id)
		except Department.DoesNotExist:
			raise ValidationError({"department_id": "Invalid department id"})

	# Determine base salary and expected working days
	base_salary = data.base_salary if data.base_salary is not None else ROLE_BASE_SALARIES.get(role.role, 0)
	expected_working_days = data.expected_working_days if data.expected_working_days is not None else 22

	try:
		with transaction.atomic():
			employee = Employee.objects.create(
				email=data.email,
				password=make_password(data.password),
				first_name=data.first_name,
				last_name=data.last_name,
				cnp=data.cnp,
				role=role,
				manager=manager,
				department=department,
				base_salary=base_salary,
				expected_working_days=expected_working_days,
			)

			# Create an initial Attendance row for the current month/year.
			# Use provided working_days/leave_days when available; otherwise
			# default working_days -> expected_working_days, leave_days -> 0.
			wd = getattr(data, 'working_days', None)
			ld = getattr(data, 'leave_days', None)
			if wd is None:
				wd = expected_working_days or 0
			if ld is None:
				ld = 0
			# Attendance model will set year/month defaults automatically.
			Attendance.objects.create(employee=employee, working_days=wd, leave_days=ld)
	except IntegrityError as e:
		raise ValidationError({"detail": f"Database constraint error: {str(e)}"})
	return employee

def get_employee(employee_id: int) -> Employee:
    """Retrieve an Employee by ID."""
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        raise ValidationError({"employee_id": "Employee not found"})
    return employee


def get_all_employees() -> list[Employee]:
    """Retrieve all Employees."""
    return list(Employee.objects.all())


def serialize_employee(employee: Employee) -> EmployeeSchema:
	return EmployeeSchema(
		id=employee.id,
		email=employee.email,
		first_name=employee.first_name,
		last_name=employee.last_name,
		cnp=employee.cnp,
		role=EmployeeRoleSchema(id=employee.role.id, role=employee.role.role),
		manager_id=employee.manager.id if employee.manager else None,
		department_id=employee.department.id if employee.department else None,
		base_salary=float(employee.base_salary),
		expected_working_days=employee.expected_working_days,
	)

def update_employee(employee_id: int, data: EmployeeUpdateSchema) -> Employee:
	"""Partial update employee fields; password re-hashed if provided."""
	employee = get_employee(employee_id)
	changed = False
	if data.first_name is not None:
		employee.first_name = data.first_name; changed = True
	if data.last_name is not None:
		employee.last_name = data.last_name; changed = True
	if data.role_id is not None:
		from app.db.models import EmployeeRole
		try:
			role = EmployeeRole.objects.get(id=data.role_id)
		except EmployeeRole.DoesNotExist:
			raise ValidationError({"role_id": "Invalid role id"})
		employee.role = role; changed = True
	if data.manager_id is not None:
		if data.manager_id == 0:
			employee.manager = None; changed = True
		else:
			try:
				mgr = Employee.objects.get(id=data.manager_id)
			except Employee.DoesNotExist:
				raise ValidationError({"manager_id": "Invalid manager id"})
			employee.manager = mgr; changed = True
	if data.department_id is not None:
		if data.department_id == 0:
			employee.department = None; changed = True
		else:
			from app.db.models import Department
			try:
				dep = Department.objects.get(id=data.department_id)
			except Department.DoesNotExist:
				raise ValidationError({"department_id": "Invalid department id"})
			employee.department = dep; changed = True
	if data.base_salary is not None:
		employee.base_salary = data.base_salary; changed = True
	if data.expected_working_days is not None:
		employee.expected_working_days = data.expected_working_days; changed = True
	if data.password is not None:
		employee.password = make_password(data.password); changed = True
	if changed:
		employee.save()
	return employee

__all__ = [name for name in (__name__,)]
