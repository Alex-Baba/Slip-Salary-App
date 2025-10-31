from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied
from app.services.auth_utils import get_current_employee, employee_is_manager, employee_is_admin

class MeView(APIView):
    def get(self, request):
        try:
            emp = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        base = {
            "id": emp.id,
            "email": emp.email,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "role": emp.role.role if emp.role else None,
            "department": emp.department.name if emp.department else None,
        }
        if employee_is_admin(emp):
            data = {
                **base,
                "permissions": ["admin", "manager", "employee"],
                "managed_departments": [emp.department.name] if emp.department else [],
                "subordinates": [
                    {"id": s.id, "first_name": s.first_name, "last_name": s.last_name, "department": s.department.name if s.department else None}
                    for s in emp.subordinates.all()
                ],
            }
        elif employee_is_manager(emp):
            data = {
                **base,
                "permissions": ["manager", "employee"],
                "subordinates_count": emp.subordinates.count(),
                "subordinates": [
                    {"id": s.id, "first_name": s.first_name, "last_name": s.last_name}
                    for s in emp.subordinates.all()
                ],
            }
        else:
            data = {**base, "permissions": ["employee"]}
        return Response(data, status=status.HTTP_200_OK)

__all__ = ["MeView"]