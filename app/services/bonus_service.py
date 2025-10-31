from app.api.schemas import BonusCreateSchema, BonusSchema, BonusUpdateSchema
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

def update_bonus(bonus_id: int, data: BonusUpdateSchema) -> Bonus:
    try:
        bonus = Bonus.objects.get(id=bonus_id)
    except Bonus.DoesNotExist:
        raise ValidationError({"bonus_id": "Bonus not found"})
    if data.amount is not None:
        if data.amount <= 0:
            raise ValidationError({"amount": "Bonus amount must be positive"})
        bonus.amount = data.amount
    if data.description is not None:
        if not data.description:
            raise ValidationError({"description": "Description cannot be empty"})
        bonus.description = data.description
    if data.date is not None:
        try:
            new_date = data.to_date()
        except ValueError as ve:
            raise ValidationError({"date": str(ve)})
        if new_date:
            bonus.date = new_date
    bonus.save()
    return bonus

def delete_bonus(bonus_id: int) -> Bonus:
    try:
        bonus = Bonus.objects.get(id=bonus_id)
    except Bonus.DoesNotExist:
        raise ValidationError({"bonus_id": "Bonus not found"})
    b = bonus
    bonus.delete()
    return b

__all__ = ["create_bonus", "update_bonus", "delete_bonus"]