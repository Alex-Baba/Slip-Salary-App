from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError, PermissionDenied
from pydantic import ValidationError as PydanticValidationError
from datetime import datetime

from app.services.attendance_service import upsert_attendance, update_attendance, list_attendance
from app.api.schemas import AttendanceCreateSchema, AttendanceUpdateSchema, AttendanceSchema, EmployeeRoleSchema
from app.services.auth_utils import get_current_employee, can_manage_employee

class AttendanceUpsertView(APIView):
    def post(self, request):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            payload = AttendanceCreateSchema(**request.data)
        except PydanticValidationError as e:
            return Response({"pydantic_errors": e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        # Only allow actor to modify own or managed employee attendance
        from app.db.models import Employee
        try:
            target = Employee.objects.get(id=payload.employee_id)
        except Employee.DoesNotExist:
            return Response({"model_errors": {"employee_id": "Employee not found"}}, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_employee(actor, target):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        try:
            att = upsert_attendance(payload)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AttendanceSchema.model_validate(att).dict(), status=status.HTTP_200_OK)

class AttendanceUpdateView(APIView):
    def patch(self, request, attendance_id: int):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            payload = AttendanceUpdateSchema(**request.data)
        except PydanticValidationError as e:
            return Response({"pydantic_errors": e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        try:
            att = update_attendance(attendance_id, payload)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure RBAC on target employee
        from app.db.models import Attendance as AttModel
        try:
            att_obj = AttModel.objects.get(id=attendance_id)
        except AttModel.DoesNotExist:
            return Response({"model_errors": {"attendance_id": "Attendance record not found"}}, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_employee(actor, att_obj.employee):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        return Response(AttendanceSchema.model_validate(att).dict(), status=status.HTTP_200_OK)

class AttendanceListView(APIView):
    def get(self, request):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        today = datetime.today()
        try:
            month = int(month) if month is not None else today.month
            year = int(year) if year is not None else today.year
        except ValueError:
            return Response({"query_errors": {"month/year": "Must be integers"}}, status=status.HTTP_400_BAD_REQUEST)

        # If employee param provided filter and RBAC
        employee_id = request.query_params.get('employee_id')
        records = list_attendance(year=year, month=month)
        if employee_id is not None:
            try:
                eid = int(employee_id)
            except ValueError:
                return Response({"query_errors": {"employee_id": "Must be integer"}}, status=status.HTTP_400_BAD_REQUEST)
            from app.db.models import Employee
            try:
                target = Employee.objects.get(id=eid)
            except Employee.DoesNotExist:
                return Response({"query_errors": {"employee_id": "Employee not found"}}, status=status.HTTP_404_NOT_FOUND)
            if not can_manage_employee(actor, target):
                return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
            records = [r for r in records if r.employee_id == eid]
        else:
            # Non-admins only see their own unless manager (then department filtering optional - keep all department records)
            if not can_manage_employee(actor, actor):
                return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
            # If plain employee restrict to own
            if actor.subordinates.count() == 0 and actor.role and actor.role.role.lower() not in ("admin", "manager"):
                records = [r for r in records if r.employee_id == actor.id]
        serialized = [AttendanceSchema.model_validate(r).dict() for r in records]
        return Response(serialized, status=status.HTTP_200_OK)
