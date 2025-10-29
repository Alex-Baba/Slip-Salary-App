from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError
from datetime import datetime

from app.services.attendance_service import upsert_attendance, update_attendance, list_attendance
from app.api.schemas import AttendanceCreateSchema, AttendanceUpdateSchema, AttendanceSchema, EmployeeRoleSchema

class AttendanceUpsertView(APIView):
    def post(self, request):
        try:
            payload = AttendanceCreateSchema(**request.data)
        except PydanticValidationError as e:
            return Response({"pydantic_errors": e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        try:
            att = upsert_attendance(payload)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AttendanceSchema.model_validate(att).dict(), status=status.HTTP_200_OK)

class AttendanceUpdateView(APIView):
    def patch(self, request, attendance_id: int):
        try:
            payload = AttendanceUpdateSchema(**request.data)
        except PydanticValidationError as e:
            return Response({"pydantic_errors": e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        try:
            att = update_attendance(attendance_id, payload)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AttendanceSchema.model_validate(att).dict(), status=status.HTTP_200_OK)

class AttendanceListView(APIView):
    def get(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        today = datetime.today()
        try:
            month = int(month) if month is not None else today.month
            year = int(year) if year is not None else today.year
        except ValueError:
            return Response({"query_errors": {"month/year": "Must be integers"}}, status=status.HTTP_400_BAD_REQUEST)

        records = list_attendance(year=year, month=month)
        serialized = [AttendanceSchema.model_validate(r).dict() for r in records]
        return Response(serialized, status=status.HTTP_200_OK)
