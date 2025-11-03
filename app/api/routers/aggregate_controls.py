from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError, PermissionDenied
from django.conf import settings
from app.services.auth_utils import get_current_employee, employee_is_manager, employee_is_admin, can_manage_employee
from app.services.sendAggregatedEmployeeData_service import (
    fetch_aggregated_employee_data, generate_employee_csv, save_aggregate_csv, get_aggregate_filepath,
    generate_manager_csv
)
from app.db.models import Employee
import os
from datetime import datetime


class EmployeeGenerateAggregateView(APIView):
    def post(self, request, employee_id: int):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            target = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        if not (employee_is_admin(actor) or can_manage_employee(actor, target)):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        year = request.data.get('year') or request.query_params.get('year')
        month = request.data.get('month') or request.query_params.get('month')
        y_int = int(year) if year is not None else None
        m_int = int(month) if month is not None else None
        try:
            aggregated = fetch_aggregated_employee_data(employee_id, y_int, m_int)
            csv_bytes = generate_employee_csv(aggregated)
            saved = save_aggregate_csv(employee_id, csv_bytes, y_int, m_int)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"saved_path": saved}, status=status.HTTP_200_OK)


class EmployeeAggregateStatusView(APIView):
    def get(self, request, employee_id: int):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            target = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        if not (employee_is_admin(actor) or actor.id == target.id or can_manage_employee(actor, target)):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        y_int = int(year) if year is not None else None
        m_int = int(month) if month is not None else None
        try:
            path = get_aggregate_filepath(employee_id, y_int, m_int)
            if os.path.exists(path):
                mtime = os.path.getmtime(path)
                return Response({"exists": True, "last_generated": datetime.fromtimestamp(mtime).isoformat(), "path": path}, status=status.HTTP_200_OK)
            else:
                return Response({"exists": False, "last_generated": None}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"exists": False, "last_generated": None}, status=status.HTTP_200_OK)


class ManagerGenerateTeamAggregateView(APIView):
    def post(self, request, manager_id: int):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not (employee_is_manager(actor) or employee_is_admin(actor)):
            return Response({"error": "Manager or Admin required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            manager = Employee.objects.get(id=manager_id)
        except Employee.DoesNotExist:
            return Response({"error": "Manager not found"}, status=status.HTTP_404_NOT_FOUND)
        year = request.data.get('year') or request.query_params.get('year')
        month = request.data.get('month') or request.query_params.get('month')
        y_int = int(year) if year is not None else None
        m_int = int(month) if month is not None else None
        subs = Employee.objects.filter(manager_id=manager_id).order_by('id')
        if not subs.exists():
            return Response({"manager_id": manager_id, "saved": False, "error": "No subordinates"}, status=status.HTTP_200_OK)
        rows = []
        try:
            for emp in subs:
                rows.append(fetch_aggregated_employee_data(emp.id, y_int, m_int))
            csv_bytes = generate_manager_csv(rows)
            base = getattr(settings, 'MEDIA_ROOT', None) or os.path.join(settings.BASE_DIR, 'media')
            dirpath = os.path.join(base, 'aggregates', f"{y_int or datetime.today().year}-{(m_int or datetime.today().month):02d}")
            os.makedirs(dirpath, exist_ok=True)
            filename = f"manager_{manager_id}_team_aggregate.csv"
            path = os.path.join(dirpath, filename)
            with open(path, 'wb') as fh:
                fh.write(csv_bytes)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"saved_path": path}, status=status.HTTP_200_OK)


class ManagerAggregateStatusView(APIView):
    def get(self, request, manager_id: int):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not (employee_is_admin(actor) or actor.id == manager_id or employee_is_manager(actor)):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        y_int = int(year) if year is not None else None
        m_int = int(month) if month is not None else None
        base = getattr(settings, 'MEDIA_ROOT', None) or os.path.join(settings.BASE_DIR, 'media')
        dirpath = os.path.join(base, 'aggregates', f"{y_int or datetime.today().year}-{(m_int or datetime.today().month):02d}")
        filename = f"manager_{manager_id}_team_aggregate.csv"
        path = os.path.join(dirpath, filename)
        if os.path.exists(path):
            mtime = os.path.getmtime(path)
            return Response({"exists": True, "last_generated": datetime.fromtimestamp(mtime).isoformat(), "path": path}, status=status.HTTP_200_OK)
        return Response({"exists": False, "last_generated": None}, status=status.HTTP_200_OK)


__all__ = [
    'EmployeeGenerateAggregateView', 'EmployeeAggregateStatusView',
    'ManagerGenerateTeamAggregateView', 'ManagerAggregateStatusView'
]
