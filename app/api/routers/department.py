from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError

from app.services.department_service import create_department, get_all_departments
from app.api.schemas import DepartmentSchema, DepartmentCreateSchema

class DepartmentCreateView(APIView):
    def post(self, request):
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
        departments = get_all_departments()
        serialized = [DepartmentSchema.model_validate(dep).dict() for dep in departments]
        return Response(serialized, status=status.HTTP_200_OK)
