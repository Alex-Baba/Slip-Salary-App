from django.core.exceptions import ValidationError
from app.db.models import Attendance, Employee
from app.services.salary_service import compute_monthly_salary

def generate_aggregate_employee_report(employee_id: int, year: int, month: int) -> dict:
    """Aggregate employee data including personal info and attendance for a given month and year."""
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        raise ValidationError({"employee_id": "Employee not found"})

    attendance = Attendance.objects.filter(employee=employee, year=year, month=month).first()

    monthly_salary = compute_monthly_salary(employee, year, month)

    aggregated_data = {
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": employee.email,
        "role": employee.role.role,
        "department": employee.department.name if employee.department else None,
        "manager": f"{employee.manager.first_name} {employee.manager.last_name}" if employee.manager else None,
        "salary": monthly_salary,
        "currency": "EUR",
        "attendance": {
            "year": year,
            "month": month,
            "working_days": attendance.working_days if attendance else 0,
            "leave_days": attendance.leave_days if attendance else 0,
        }
    }

    return aggregated_data

__all__ = ["generate_aggregate_employee_report"]

