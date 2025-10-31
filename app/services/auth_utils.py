import os, jwt
from typing import Optional
from django.core.exceptions import PermissionDenied
from app.db.models import Employee, EmployeeRole

JWT_SECRET = os.environ.get('JWT_SECRET', 'dev_jwt_secret')
JWT_ALG = 'HS256'

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise PermissionDenied("Token expired")
    except jwt.InvalidTokenError:
        raise PermissionDenied("Invalid token")

def extract_token_from_request(request) -> Optional[str]:
    auth_header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION')
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == 'bearer':
        return parts[1]
    return None

def get_current_employee(request) -> Employee:
    token = extract_token_from_request(request)
    if not token:
        raise PermissionDenied("Authentication required")
    payload = decode_token(token)
    user_id = payload.get('sub')
    try:
        return Employee.objects.get(id=user_id)
    except Employee.DoesNotExist:
        raise PermissionDenied("User not found")

def employee_is_manager(employee: Employee) -> bool:
    # Manager if has subordinates or holds a role named 'manager' (case-insensitive)
    if employee.subordinates.exists():
        return True
    role_name = (employee.role.role if employee.role else '').lower()
    return role_name in ('manager', 'team lead', 'lead')

def employee_is_admin(employee: Employee) -> bool:
    role_name = (employee.role.role if employee.role else '').lower()
    return role_name in ('admin', 'administrator')

def require_manager(request):
    emp = get_current_employee(request)
    if not employee_is_manager(emp):
        raise PermissionDenied("Manager privileges required")
    return emp

def require_admin(request):
    emp = get_current_employee(request)
    if not employee_is_admin(emp):
        raise PermissionDenied("Admin privileges required")
    return emp

def require_admin_or_manager(request):
    emp = get_current_employee(request)
    if employee_is_admin(emp) or employee_is_manager(emp):
        return emp
    raise PermissionDenied("Manager or Admin privileges required")

def can_manage_employee(actor: Employee, target: Employee) -> bool:
    """Return True if actor can manage target per RBAC rules.
    Admin: any employee.
    Manager: employees within same department (optionally could narrow to subordinates; using department per requirement).
    """
    if actor.id == target.id:
        return True  # self
    if employee_is_admin(actor):
        return True
    if employee_is_manager(actor) and actor.department_id and actor.department_id == target.department_id:
        return True
    return False

__all__ = [
    "decode_token", "extract_token_from_request", "get_current_employee",
    "employee_is_manager", "employee_is_admin", "require_manager", "require_admin",
    "require_admin_or_manager", "can_manage_employee"
]
