from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from app.services.sendAggregatedEmployeeData_service import send_manager_aggregated_csv_email
from app.services.idempotency_service import get_or_create_idempotent
from app.services.auth_utils import get_current_employee, employee_is_manager, employee_is_admin
import logging
from app.db.models import Employee

logger = logging.getLogger('send')

class SendManagerAggregatedCsvEmailView(APIView):
	def post(self, request):
		# Only managers can call this endpoint (regardless of target manager_id)
		try:
			caller = get_current_employee(request)
		except Exception as e:
			return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
		if not (employee_is_manager(caller) or employee_is_admin(caller)):
			return Response({"error": "Manager or Admin privileges required"}, status=status.HTTP_403_FORBIDDEN)
		manager_id = request.data.get('manager_id') or request.query_params.get('manager_id')
		if manager_id is None:
			return Response({"errors": {"manager_id": "Provide manager_id"}}, status=status.HTTP_400_BAD_REQUEST)
		try:
			manager_id_int = int(manager_id)
		except ValueError:
			return Response({"errors": {"manager_id": "Must be integer"}}, status=status.HTTP_400_BAD_REQUEST)
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
		to_email = request.data.get('send_to') or request.query_params.get('send_to')  # optional override
		key = request.headers.get('Idempotency-Key') or request.headers.get('IDEMPOTENCY_KEY')
		payload = {"manager_id": manager_id_int, "year": y_int, "month": m_int, "send_to": to_email}
		def build_response():
			try:
				return send_manager_aggregated_csv_email(manager_id_int, y_int, m_int, to_email)
			except ValidationError as e:
				details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
				raise ValidationError(details)
		if key:
			idem = get_or_create_idempotent('send-manager-aggregate', key, payload, build_response, owner=caller)
			if idem.get('conflict'):
				return Response(idem, status=status.HTTP_409_CONFLICT)
			result = idem['data'] | {"idempotent": idem['idempotent'], "cached": idem['cached']}
			# Log who requested and who received
			try:
				recipient = Employee.objects.get(id=manager_id_int).email
			except Employee.DoesNotExist:
				recipient = None
			payload = {
				'actor_id': getattr(caller, 'id', None),
				'actor_email': getattr(caller, 'email', None),
				'manager_id': manager_id_int,
				'recipient': recipient,
				'idempotency_key': key,
				'provider_response': result.get('provider_response') or result.get('archive_path') or result,
			}
			logger.info('send_manager_aggregate %s', __import__('json').dumps(payload, default=str))
			return Response(result, status=status.HTTP_200_OK)
		else:
			try:
				result = send_manager_aggregated_csv_email(manager_id_int, y_int, m_int, to_email)
			except ValidationError as e:
				details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
				return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)
			return Response(result, status=status.HTTP_200_OK)

__all__ = ["SendManagerAggregatedCsvEmailView"]