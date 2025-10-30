from app.api.schemas import BonusCreateSchema, BonusSchema
from app.db.models import Bonus, Employee
from django.core.exceptions import ValidationError
from datetime import date

def create_bonus(data: BonusCreateSchema) -> Bonus:
    # Validate employee
    try:
        employee = Employee.objects.get(id=data.employee_id)
    except Employee.DoesNotExist:
        raise ValidationError({"employee_id": "Employee not found"})

    # Basic constraints
    if data.amount <= 0:
        raise ValidationError({"amount": "Bonus amount must be positive"})
    if not data.description:
        raise ValidationError({"reason": "Reason for bonus cannot be empty"})

    # Convert provided date string or default to today using schema helper
    try:
        bonus_date = data.to_date()
    except ValueError as ve:
        raise ValidationError({"date": str(ve)})

    bonus = Bonus.objects.create(
        employee=employee,
        amount=data.amount,
        description=data.description,
        date=bonus_date
    )
    return bonus

__all__ = ["create_bonus"]