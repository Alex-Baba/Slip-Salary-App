from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError, PermissionDenied
from pydantic import ValidationError as PydanticValidationError

from app.services.department_service import create_department, get_all_departments, update_department, delete_department
from app.api.schemas import DepartmentSchema, DepartmentCreateSchema, DepartmentUpdateSchema
from app.services.auth_utils import get_current_employee, employee_is_admin

class DepartmentCreateView(APIView):
    def post(self, request):
        # Admin only
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not employee_is_admin(actor):
            return Response({"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            payload = DepartmentCreateSchema(**request.data)
        except PydanticValidationError as e:
            return Response({"pydantic_errors": e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        try:
            department = create_department(payload)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)

        return Response(DepartmentSchema.from_orm(department).dict(), status=status.HTTP_201_CREATED)

class DepartmentListView(APIView):
    def get(self, request):
        # Admin only list
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not employee_is_admin(actor):
            return Response({"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN)
        departments = get_all_departments()
        serialized = [DepartmentSchema.model_validate(dep).dict() for dep in departments]
        return Response(serialized, status=status.HTTP_200_OK)

class DepartmentUpdateView(APIView):
    def patch(self, request, department_id: int):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not employee_is_admin(actor):
            return Response({"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            payload = DepartmentUpdateSchema(**request.data)
        except PydanticValidationError as e:
            return Response({"pydantic_errors": e.errors()}, status=status.HTTP_400_BAD_REQUEST)
        try:
            dep = update_department(department_id, payload)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)
        return Response(DepartmentSchema.from_orm(dep).dict(), status=status.HTTP_200_OK)

class DepartmentDeleteView(APIView):
    def delete(self, request, department_id: int):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not employee_is_admin(actor):
            return Response({"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            dep_snapshot = delete_department(department_id)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_404_NOT_FOUND)
        return Response(dep_snapshot, status=status.HTTP_200_OK)
