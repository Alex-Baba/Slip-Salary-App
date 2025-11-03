from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError, PermissionDenied
from app.services.auth_utils import get_current_employee, employee_is_manager, employee_is_admin
from app.services.employee_service import get_all_employees, serialize_employee
from app.services.createPdfForEmployees_service import create_pdf_for_employee, save_payslip_pdf, get_payslip_filepath
import os
from datetime import datetime
from app.services.sendPdfForEmployees_service import send_payslip_email
from app.db.models import Employee


class DepartmentMyEmployeesView(APIView):
    def get(self, request):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        # Only manager or admin
        if not (employee_is_manager(actor) or employee_is_admin(actor)):
            return Response({"error": "Manager or admin required"}, status=status.HTTP_403_FORBIDDEN)
        dept_id = actor.department_id
        if not dept_id:
            return Response({"error": "Actor has no department"}, status=status.HTTP_400_BAD_REQUEST)
        # Exclude the actor (manager) from their own department employee listing
        qs = Employee.objects.filter(department_id=dept_id).exclude(id=actor.id)
        serialized: list[dict] = []
        for e in qs:
            item = serialize_employee(e).dict()
            try:
                path = get_payslip_filepath(e.id)
                if os.path.exists(path):
                    mtime = os.path.getmtime(path)
                    item['payslip_exists'] = True
                    item['payslip_last_generated'] = datetime.fromtimestamp(mtime).isoformat()
                else:
                    item['payslip_exists'] = False
                    item['payslip_last_generated'] = None
            except Exception:
                # Fail-safe: don't break listing if filesystem check fails
                item['payslip_exists'] = False
                item['payslip_last_generated'] = None
            serialized.append(item)
        return Response(serialized, status=status.HTTP_200_OK)


class EmployeeGeneratePdfView(APIView):
    def post(self, request, employee_id: int):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        # Only admin or manager of that department may generate
        try:
            target = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        # Reuse can_manage_employee from auth_utils: manager must be same department
        from app.services.auth_utils import can_manage_employee
        if not (employee_is_admin(actor) or can_manage_employee(actor, target)):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        try:
            pdf_bytes = create_pdf_for_employee(employee_id=employee_id)
            saved = save_payslip_pdf(employee_id, pdf_bytes)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"saved_path": saved}, status=status.HTTP_200_OK)


class EmployeeSendPayslipView(APIView):
    def post(self, request, employee_id: int):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            target = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        from app.services.auth_utils import can_manage_employee
        if not (employee_is_admin(actor) or can_manage_employee(actor, target)):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        try:
            resp = send_payslip_email(employee_id)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)
        return Response(resp, status=status.HTTP_200_OK)
