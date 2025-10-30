from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from app.services.sendAggregatedEmployeeData_service import send_aggregated_csv_email

class SendAggregatedCsvEmailView(APIView):
    def post(self, request):
        employee_id = request.data.get('employee_id') or request.query_params.get('employee_id')
        if employee_id is None:
            return Response({"errors": {"employee_id": "Provide employee_id"}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employee_id_int = int(employee_id)
        except ValueError:
            return Response({"errors": {"employee_id": "Must be integer"}}, status=status.HTTP_400_BAD_REQUEST)
        year = request.data.get('year') or request.query_params.get('year')
        month = request.data.get('month') or request.query_params.get('month')
        y_int = None
        m_int = None
        try:
            if year is not None:
                y_int = int(year)
            if month is not None:
                m_int = int(month)
        except ValueError:
            return Response({"errors": {"year/month": "Must be integers"}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = send_aggregated_csv_email(employee_id_int, y_int, m_int)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)

__all__ = ["SendAggregatedCsvEmailView"]
