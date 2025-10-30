from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from app.services.auth_service import authenticate

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({'errors': {'email/password': 'Both email and password required'}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = authenticate(email=email, password=password)
        except ValidationError as e:
            details = e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)}
            return Response({'model_errors': details}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_200_OK)

__all__ = ['LoginView']
