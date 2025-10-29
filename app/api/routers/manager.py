from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError

from app.services.manager_service import get_all_managers, get_department_managers

class ManagerListView(APIView):
    def get(self, request):
        managers = get_all_managers()
        serialized = [  # Using dict() to convert Pydantic models to dictionaries
            {
                "id": mgr.id,
                "first_name": mgr.first_name,
                "last_name": mgr.last_name,
                "department_name": mgr.department_name
            }
            for mgr in managers
        ]
        return Response(serialized, status=status.HTTP_200_OK)

class DepartmentManagersView(APIView):
    def get(self, request, department_id):
        try:
            managers = get_department_managers(department_id)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)

        serialized = [
            {
                "id": mgr.id,
                "first_name": mgr.first_name,
                "last_name": mgr.last_name,
                "department_name": mgr.department_name
            }
            for mgr in managers
        ]
        return Response(serialized, status=status.HTTP_200_OK)