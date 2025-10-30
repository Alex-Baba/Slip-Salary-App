from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError
from datetime import datetime

from app.services.aggregateEmployeeData_service import generate_aggregate_employee_report
# Generates a report of employee data aggregated from multiple sources.

class AggregateEmployeeDataView(APIView):
    def get(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        today = datetime.today()
        try:
            month = int(month) if month is not None else today.month
            year = int(year) if year is not None else today.year
        except ValueError:
            return Response({"query_errors": {"month/year": "Must be integers"}}, status=status.HTTP_400_BAD_REQUEST)

        employee_id = request.query_params.get('employee_id')
        if employee_id is None:
            return Response({"query_errors": {"employee_id": "Provide employee_id for aggregation."}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employee_id_int = int(employee_id)
        except ValueError:
            return Response({"query_errors": {"employee_id": "Must be integer"}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = generate_aggregate_employee_report(employee_id=employee_id_int, year=year, month=month)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_200_OK)
