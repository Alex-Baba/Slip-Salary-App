from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError
from app.api.schemas import EmployeeCreateSchema
from app.services.employee_service import create_employee, serialize_employee, get_all_employees


class EmployeeCreateView(APIView):
    def post(self, request):
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
        employees = get_all_employees()
        serialized_employees = [serialize_employee(emp).dict() for emp in employees]
        return Response(serialized_employees, status=status.HTTP_200_OK)

  