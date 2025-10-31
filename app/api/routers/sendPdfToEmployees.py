from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from app.services.sendPdfForEmployees_service import send_payslip_email
from app.services.idempotency_service import get_or_create_idempotent
from app.services.auth_utils import get_current_employee, employee_is_manager, employee_is_admin, can_manage_employee

class SendPayslipEmailView(APIView):
    def post(self, request):
        # Auth: allow employee to fetch own payslip; manager can fetch any.
        try:
            current = get_current_employee(request)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        employee_id = request.data.get('employee_id') or request.query_params.get('employee_id')
        if employee_id is None:
            return Response({"errors": {"employee_id": "Provide employee_id"}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employee_id_int = int(employee_id)
        except ValueError:
            return Response({"errors": {"employee_id": "Must be integer"}}, status=status.HTTP_400_BAD_REQUEST)
        key = request.headers.get('Idempotency-Key') or request.headers.get('IDEMPOTENCY_KEY')
        def build_response():
            try:
                return send_payslip_email(employee_id_int)
            except ValidationError as e:
                details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
                # propagate error directly (not cached)
                raise ValidationError(details)
        if key:
            idem_result = get_or_create_idempotent(
                endpoint='send-payslip',
                key=key,
                request_payload={'employee_id': employee_id_int},
                response_builder=build_response
            )
            if idem_result.get('conflict'):
                return Response(idem_result, status=status.HTTP_409_CONFLICT)
            return Response(idem_result['data'] | {"idempotent": idem_result['idempotent'], "cached": idem_result['cached']}, status=status.HTTP_200_OK)
        else:
            # Authorization: if not manager and requesting someone else -> forbidden
            if employee_id_int != current.id:
                from app.db.models import Employee
                try:
                    target = Employee.objects.get(id=employee_id_int)
                except Employee.DoesNotExist:
                    return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
                if not can_manage_employee(current, target):
                    return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
            try:
                result = send_payslip_email(employee_id_int)
            except ValidationError as e:
                details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
                return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)
            return Response(result, status=status.HTTP_200_OK)

__all__ = ["SendPayslipEmailView"]
