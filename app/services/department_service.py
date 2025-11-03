from django.core.exceptions import ValidationError
from django.db import IntegrityError
from app.db.models import Department
from app.api.schemas import DepartmentSchema, DepartmentCreateSchema, DepartmentUpdateSchema

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

def update_department(department_id: int, data: DepartmentUpdateSchema) -> Department:
    try:
        dep = Department.objects.get(id=department_id)
    except Department.DoesNotExist:
        raise ValidationError({"department_id": "Department not found"})
    if data.name is not None:
        # uniqueness check
        if Department.objects.exclude(id=department_id).filter(name=data.name).exists():
            raise ValidationError({"name": "Department name already in use"})
        dep.name = data.name
    dep.save()
    return dep

def delete_department(department_id: int) -> dict:
    try:
        dep = Department.objects.get(id=department_id)
    except Department.DoesNotExist:
        raise ValidationError({"department_id": "Department not found"})
    # Take a simple snapshot before deleting to avoid serializing a deleted ORM instance later
    from app.api.schemas import DepartmentSchema
    dep_snapshot = DepartmentSchema.model_validate(dep).dict()
    dep.delete()
    return dep_snapshot