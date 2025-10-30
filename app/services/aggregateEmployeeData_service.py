from django.core.exceptions import ValidationError
from app.db.models import Attendance, Employee, Bonus
from app.services.salary_service import compute_monthly_salary, _business_days_in_month

def generate_aggregate_employee_report(employee_id: int, year: int, month: int) -> dict:
    """Aggregate employee data including personal info and attendance for a given month and year."""
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        raise ValidationError({"employee_id": "Employee not found"})

    attendance = Attendance.objects.filter(employee=employee, year=year, month=month).first()

    # Total (with bonuses) using existing service
    total_salary = compute_monthly_salary(employee, year, month)

    bonuses_qs = Bonus.objects.filter(employee=employee, date__year=year, date__month=month).order_by('date')
    bonuses_list = [
        {
            "amount": float(b.amount),
            "description": b.description,
            "date": b.date.isoformat()
        } for b in bonuses_qs
    ]
    total_bonus = round(sum(b["amount"] for b in bonuses_list), 2)

    # Recompute base prorated salary without bonuses (mirror logic from salary_service sans bonuses)
    expected_days = employee.expected_working_days
    if expected_days is None:
        expected_days = _business_days_in_month(year, month)
    if expected_days and expected_days > 0:
        daily_rate = float(employee.base_salary) / expected_days
    else:
        daily_rate = 0
    working_days = attendance.working_days if attendance else 0
    leave_days = attendance.leave_days if attendance else 0
    prorated_base = daily_rate * working_days
    unpaid_leave_adjust = daily_rate * leave_days
    salary_without_bonus = round(prorated_base - unpaid_leave_adjust, 2)

    aggregated_data = {
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": employee.email,
        "role": employee.role.role,
        "department": employee.department.name if employee.department else None,
        "manager": f"{employee.manager.first_name} {employee.manager.last_name}" if employee.manager else None,
        "attendance": {
            "year": year,
            "month": month,
            "working_days": attendance.working_days if attendance else 0,
            "leave_days": attendance.leave_days if attendance else 0,
        },
        "bonuses": bonuses_list,
        "total_bonus": total_bonus,
        "salary": salary_without_bonus,
        "total_salary": total_salary
    }

    return aggregated_data

__all__ = ["generate_aggregate_employee_report"]

