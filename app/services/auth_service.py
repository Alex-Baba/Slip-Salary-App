import os, jwt, datetime
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from app.db.models import Employee

JWT_SECRET = os.environ.get('JWT_SECRET', 'dev_jwt_secret')
JWT_ALG = 'HS256'
JWT_EXP_MINUTES = int(os.environ.get('JWT_EXP_MINUTES', '60'))

def authenticate(email: str, password: str) -> dict:
    try:
        user = Employee.objects.get(email=email)
    except Employee.DoesNotExist:
        raise ValidationError({'email': 'Invalid credentials'})
    if not check_password(password, user.password):
        raise ValidationError({'password': 'Invalid credentials'})
    exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXP_MINUTES)
    payload = {'sub': user.id, 'email': user.email, 'exp': exp}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return {'token': token, 'user_id': user.id}

__all__ = ['authenticate']
