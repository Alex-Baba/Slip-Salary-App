from django.core.exceptions import ValidationError
from django.db import IntegrityError
from app.db.models import Attendance, Employee
from app.api.schemas import AttendanceCreateSchema, AttendanceUpdateSchema, AttendanceSchema


def upsert_attendance(data: AttendanceCreateSchema) -> Attendance:
    # Validate employee
    try:
        employee = Employee.objects.get(id=data.employee_id)
    except Employee.DoesNotExist:
        raise ValidationError({"employee_id": "Employee not found"})

    # Basic constraints
    if data.working_days < 0:
        raise ValidationError({"working_days": "Cannot be negative"})
    if data.leave_days < 0:
        raise ValidationError({"leave_days": "Cannot be negative"})
    if data.month < 1 or data.month > 12:
        raise ValidationError({"month": "Must be between 1 and 12"})
    if data.year < 2000 or data.year > 2100:
        raise ValidationError({"year": "Out of acceptable range"})

    try:
        att, created = Attendance.objects.update_or_create(
            employee=employee,
            year=data.year,
            month=data.month,
            defaults={
                "working_days": data.working_days,
                "leave_days": data.leave_days,
            }
        )
    except IntegrityError as e:
        raise ValidationError({"detail": f"Database constraint error: {str(e)}"})
    return att


def update_attendance(attendance_id: int, data: AttendanceUpdateSchema) -> Attendance:
    try:
        att = Attendance.objects.get(id=attendance_id)
    except Attendance.DoesNotExist:
        raise ValidationError({"attendance_id": "Attendance record not found"})

    if data.working_days is not None:
        if data.working_days < 0:
            raise ValidationError({"working_days": "Cannot be negative"})
        att.working_days = data.working_days

    if data.leave_days is not None:
        if data.leave_days < 0:
            raise ValidationError({"leave_days": "Cannot be negative"})
        att.leave_days = data.leave_days

    att.save()
    return att


def get_attendance(employee_id: int, year: int, month: int) -> Attendance | None:
    return Attendance.objects.filter(employee_id=employee_id, year=year, month=month).first()


def list_attendance(year: int, month: int) -> list[Attendance]:
    return list(Attendance.objects.filter(year=year, month=month).select_related('employee'))
