
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError
from django.http import HttpResponse


from app.services.createPdfForEmployees_service import create_pdf_for_employee

class CreatePdfEmployeesView(APIView):
    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        if employee_id is None:
            return Response({"query_errors": {"employee_id": "Provide employee_id to generate PDF."}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employee_id_int = int(employee_id)
        except ValueError:
            return Response({"query_errors": {"employee_id": "Must be integer"}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            pdf_content = create_pdf_for_employee(employee_id=employee_id_int)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="employee_{employee_id_int}_report.pdf"'
        response.write(pdf_content)
        return response