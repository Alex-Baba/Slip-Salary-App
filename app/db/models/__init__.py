from django.utils import timezone


def current_year():
    return timezone.now().year


def current_month():
    return timezone.now().month


# Re-export model classes from module files
from .employee import Employee
from .employee_role import EmployeeRole
from .department import Department
from .salary import Salary
from .attendance import Attendance
from .bonus import Bonus
from .idempotency import IdempotencyRecord
from .revoked_token import RevokedToken

__all__ = [
    'current_year', 'current_month',
    'Employee', 'EmployeeRole', 'Department', 'Salary', 'Attendance', 'Bonus', 'IdempotencyRecord'
    , 'RevokedToken'
]
