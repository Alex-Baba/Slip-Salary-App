
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError

from app.services.bonus_service import create_bonus
from app.api.schemas import BonusCreateSchema, BonusSchema

class BonusCreateView(APIView):
    def post(self, request):
        try:
            payload = BonusCreateSchema(**request.data)
        except PydanticValidationError as e:
            return Response({"pydantic_errors": e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        try:
            bonus = create_bonus(payload)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {"detail": str(e)}
            return Response({"model_errors": details}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BonusSchema.from_model(bonus).dict(), status=status.HTTP_201_CREATED)

class BonusListView(APIView):
    def get(self, request):
        from app.db.models import Bonus  # lightweight import here
        employee_id = request.query_params.get('employee_id')
        qs = Bonus.objects.all().order_by('-date')
        if employee_id:
            try:
                qs = qs.filter(employee_id=int(employee_id))
            except ValueError:
                return Response({"query_errors": {"employee_id": "Must be integer"}}, status=status.HTTP_400_BAD_REQUEST)
        serialized = [BonusSchema.from_model(b).dict() for b in qs]
        return Response(serialized, status=status.HTTP_200_OK)