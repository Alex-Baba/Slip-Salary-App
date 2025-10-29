from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from app.models import Employee, EmployeeRole, Department
from app.api.schemas import EmployeeCreateSchema, EmployeeSchema, EmployeeRoleSchema


def create_employee(data: EmployeeCreateSchema) -> Employee:
	"""Create an Employee from validated pydantic data.

	Steps:
	- validate role exists
	- validate manager if provided
	- hash password
	- create and return Employee instance
	"""
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

	try:
			employee = Employee.objects.create(
				email=data.email,
				password=make_password(data.password),
				first_name=data.first_name,
				last_name=data.last_name,
				cnp=data.cnp,
				role=role,
				manager=manager,
				department=department,
			)
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
	)
