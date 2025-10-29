from django.core.exceptions import ValidationError
from app.db.models import Employee, Department
from app.api.schemas import ManagerListSchema


def get_all_managers() -> list[ManagerListSchema]:
    """Retrieve all Employees with role 'manager'."""
    managers = Employee.objects.filter(role__role="manager").select_related('department')
    manager_list = []
    for manager in managers:
        manager_data = ManagerListSchema(
            id=manager.id,
            first_name=manager.first_name,
            last_name=manager.last_name,
            department_name=manager.department.name if manager.department else None
        )
        manager_list.append(manager_data)
    return manager_list

def get_department_managers(department_id: int) -> list[ManagerListSchema]:
    """Retrieve all Managers in a specific Department."""
    try:
        department = Department.objects.get(id=department_id)
    except Department.DoesNotExist:
        raise ValidationError({"department_id": "Department not found"})

    managers = Employee.objects.filter(role__role="manager", department=department).select_related('department')
    manager_list = []
    for manager in managers:
        manager_data = ManagerListSchema(
            id=manager.id,
            first_name=manager.first_name,
            last_name=manager.last_name,
            department_name=manager.department.name if manager.department else None
        )
        manager_list.append(manager_data)
    return manager_list

__all__ = ["get_all_managers", "get_department_managers"]