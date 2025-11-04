from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from app.services.auth_service import authenticate
from app.services.auth_utils import extract_token_from_request, decode_token
from app.db.models import RevokedToken

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


class LogoutView(APIView):
    def post(self, request):
        token = extract_token_from_request(request)
        if not token:
            return Response({'error': 'No token provided'}, status=status.HTTP_400_BAD_REQUEST)
        # attempt to decode to get exp
        try:
            payload = decode_token(token)
            exp_ts = payload.get('exp')
            expires_at = None
            if exp_ts:
                try:
                    import datetime
                    expires_at = datetime.datetime.utcfromtimestamp(exp_ts)
                except Exception:
                    expires_at = None
        except Exception:
            # Even if decode fails (expired/invalid), we still store the raw token to prevent reuse
            expires_at = None
        # record the revoked token
        RevokedToken.objects.get_or_create(token=token, defaults={'expires_at': expires_at})
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)

__all__.append('LogoutView')
