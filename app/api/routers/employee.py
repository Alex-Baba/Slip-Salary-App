from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError, PermissionDenied
from pydantic import ValidationError as PydanticValidationError
from app.api.schemas import EmployeeCreateSchema, EmployeeListSchema, EmployeeUpdateSchema
from app.services.employee_service import create_employee, serialize_employee, get_all_employees, get_employee, update_employee
from app.services.auth_utils import get_current_employee, employee_is_admin


class EmployeeCreateView(APIView):
    def post(self, request):
        # Only admin can create employees
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not employee_is_admin(actor):
            return Response({"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            payload = EmployeeCreateSchema(**request.data)
        except PydanticValidationError as e:
            return Response({"pydantic_errors": e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = create_employee(payload)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serialize_employee(employee).dict(), status=status.HTTP_201_CREATED)


class EmployeeListView(APIView):
    def get(self, request):
        # Admin only list
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not employee_is_admin(actor):
            return Response({"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN)
        employees = get_all_employees()
        serialized_employees = []
        for emp in employees:
            ser = serialize_employee(emp)
            list_obj = EmployeeListSchema(
                id=ser.id,
                email=ser.email,
                first_name=ser.first_name,
                last_name=ser.last_name,
                role=ser.role,
                manager_id=ser.manager_id,
                department_id=ser.department_id,
            )
            serialized_employees.append(list_obj.dict())
        return Response(serialized_employees, status=status.HTTP_200_OK)

class EmployeeDeleteView(APIView):
    def delete(self, request, employee_id: int):
        """Delete an employee and return their data (captured pre-deletion)."""
        # Admin only delete
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not employee_is_admin(actor):
            return Response({"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            employee = get_employee(employee_id)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_404_NOT_FOUND)

        # Serialize BEFORE deleting so fields like id remain intact
        serialized = serialize_employee(employee).dict()
        employee.delete()
        # Optionally could return 204 No Content; keeping 200 with payload for confirmation.
        return Response(serialized, status=status.HTTP_200_OK)

class EmployeeUpdateView(APIView):
    def patch(self, request, employee_id: int):
        # Admin only update
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not employee_is_admin(actor):
            return Response({"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            payload = EmployeeUpdateSchema(**request.data)
        except PydanticValidationError as e:
            return Response({"pydantic_errors": e.errors()}, status=status.HTTP_400_BAD_REQUEST)
        try:
            updated = update_employee(employee_id, payload)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serialize_employee(updated).dict(), status=status.HTTP_200_OK)

  