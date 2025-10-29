from django.core.exceptions import ValidationError
from django.db import IntegrityError
from app.db.models import Department
from app.api.schemas import DepartmentSchema, DepartmentCreateSchema

def create_department(data: DepartmentCreateSchema) -> Department:
    # Pre-check uniqueness to provide clearer error messages
    if Department.objects.filter(name=data.name).exists():
        raise ValidationError({"name": "Department name already in use"})

    try:
        department = Department.objects.create(
            name=data.name,
        )
    except IntegrityError as e:
        raise ValidationError({"detail": f"Database constraint error: {str(e)}"})
    return department

def get_all_departments() -> list[Department]:
    """Retrieve all Departments."""
    return list(Department.objects.all())