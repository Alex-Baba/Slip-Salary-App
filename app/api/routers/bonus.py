
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError, PermissionDenied
from pydantic import ValidationError as PydanticValidationError

from app.services.bonus_service import create_bonus, update_bonus, delete_bonus
from app.services.auth_utils import get_current_employee, employee_is_manager, employee_is_admin, can_manage_employee
from app.api.schemas import BonusCreateSchema, BonusSchema, BonusUpdateSchema

class BonusCreateView(APIView):
    def post(self, request):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            payload = BonusCreateSchema(**request.data)
        except PydanticValidationError as e:
            return Response({"pydantic_errors": e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        # RBAC: admin can create for any; manager only within same department; employee only self (rare case)
        from app.db.models import Employee
        try:
            target = Employee.objects.get(id=payload.employee_id)
        except Employee.DoesNotExist:
            return Response({"model_errors": {"employee_id": "Target employee not found"}}, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_employee(actor, target):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        try:
            bonus = create_bonus(payload)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BonusSchema.from_model(bonus).dict(), status=status.HTTP_201_CREATED)

class BonusListView(APIView):
    def get(self, request):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        from app.db.models import Bonus, Employee  # lightweight import here
        employee_id = request.query_params.get('employee_id')
        # RBAC: admin sees all; manager sees only direct reports; employee sees own.
        if employee_is_admin(actor):
            qs = Bonus.objects.all()
        elif employee_is_manager(actor):
            # Only bonuses for employees whose manager is the actor
            qs = Bonus.objects.filter(employee__manager_id=actor.id)
        else:
            qs = Bonus.objects.filter(employee_id=actor.id)
        qs = qs.order_by('-date')
        if employee_id:
            try:
                eid = int(employee_id)
                # Ensure actor has permission to view target employee bonuses
                try:
                    target = Employee.objects.get(id=eid)
                except Employee.DoesNotExist:
                    return Response({"query_errors": {"employee_id": "Employee not found"}}, status=status.HTTP_404_NOT_FOUND)
                if not can_manage_employee(actor, target):
                    return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
                qs = qs.filter(employee_id=eid)
            except ValueError:
                return Response({"query_errors": {"employee_id": "Must be integer"}}, status=status.HTTP_400_BAD_REQUEST)
        serialized = [BonusSchema.from_model(b).dict() for b in qs]
        return Response(serialized, status=status.HTTP_200_OK)

class BonusUpdateView(APIView):
    def patch(self, request, bonus_id: int):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            payload = BonusUpdateSchema(**request.data)
        except PydanticValidationError as e:
            return Response({"pydantic_errors": e.errors()}, status=status.HTTP_400_BAD_REQUEST)
        from app.db.models import Bonus
        try:
            bonus_obj = Bonus.objects.get(id=bonus_id)
        except Bonus.DoesNotExist:
            return Response({"model_errors": {"bonus_id": "Bonus not found"}}, status=status.HTTP_404_NOT_FOUND)
        # RBAC: admin any; manager if manages employee; employee only self (update their own bonus?) -> restrict to manager/admin
        if not (employee_is_admin(actor) or can_manage_employee(actor, bonus_obj.employee)):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        try:
            updated = update_bonus(bonus_id, payload)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BonusSchema.from_model(updated).dict(), status=status.HTTP_200_OK)

class BonusDeleteView(APIView):
    def delete(self, request, bonus_id: int):
        try:
            actor = get_current_employee(request)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        from app.db.models import Bonus
        try:
            bonus_obj = Bonus.objects.get(id=bonus_id)
        except Bonus.DoesNotExist:
            return Response({"model_errors": {"bonus_id": "Bonus not found"}}, status=status.HTTP_404_NOT_FOUND)
        if not (employee_is_admin(actor) or can_manage_employee(actor, bonus_obj.employee)):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        deleted = delete_bonus(bonus_id)
        return Response(BonusSchema.from_model(deleted).dict(), status=status.HTTP_200_OK)