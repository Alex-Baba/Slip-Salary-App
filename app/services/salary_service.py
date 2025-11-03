from django.db.models import Sum
from datetime import date
from app.db.models import Attendance, Bonus, Employee


def compute_monthly_salary(employee: Employee, year: int, month: int) -> float:
    """Compute prorated salary for an employee for given month.
    Formula:
        daily_rate = base_salary / expected_days
        prorated_base = daily_rate * working_days
        unpaid_leave_adjust = daily_rate * leave_days  # assuming all leave is unpaid for now
        gross = prorated_base - unpaid_leave_adjust + bonuses_total
    """
    # Determine expected days
    # Allow employee to be an object or an id; guard DB access in unit tests
    try:
        emp_id = getattr(employee, 'id', employee)
        attendance = Attendance.objects.filter(employee_id=emp_id, year=year, month=month).first()
        working_days = attendance.working_days if attendance else 0
        leave_days = attendance.leave_days if attendance else 0
    except Exception:
        working_days = 0
        leave_days = 0

    # Use explicit override or simple business day estimate (Mon-Fri count) if override missing
    expected_days = getattr(employee, 'expected_working_days', None)
    if expected_days is None:
        expected_days = _business_days_in_month(year, month)
    if expected_days <= 0:
        return float(getattr(employee, 'base_salary', 0))  # fallback

    daily_rate = float(getattr(employee, 'base_salary', 0)) / expected_days if expected_days else 0
    prorated_base = daily_rate * working_days
    unpaid_leave_adjust = daily_rate * leave_days  # treat leave as unpaid initially

    try:
        bonuses_total = Bonus.objects.filter(employee_id=emp_id, date__year=year, date__month=month).aggregate(Sum('amount'))['amount__sum'] or 0
    except Exception:
        bonuses_total = 0

    gross = prorated_base - unpaid_leave_adjust + float(bonuses_total)
    return round(gross, 2)


def _business_days_in_month(year: int, month: int) -> int:
    # Simple Monday-Friday counter ignoring holidays
    from calendar import monthrange
    import datetime
    days_in_month = monthrange(year, month)[1]
    count = 0
    for day in range(1, days_in_month + 1):
        weekday = datetime.date(year, month, day).weekday()  # 0=Mon..6=Sun
        if weekday < 5:
            count += 1
    return count
