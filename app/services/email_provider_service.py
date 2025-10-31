import os
from typing import List, Optional, Tuple
from django.core.mail import EmailMessage
from .sendgrid_service import sendgrid_available, send_sendgrid_message

FORCE_DISABLE_SENDGRID = os.getenv('SENDGRID_FORCE_DISABLE') in ('1','true','True')
EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', '').lower()  # 'sendgrid' | 'django' | ''

# Priority (default): SendGrid -> Django SMTP unless EMAIL_PROVIDER forces one.

def _send_via_django(to: List[str], subject: str, text: str, attachments: Optional[List[Tuple[str, bytes, str]]]) -> dict:
    email = EmailMessage(subject=subject, body=text, to=to)
    if attachments:
        for (filename, content_bytes, mime_type) in attachments:
            email.attach(filename=filename, content=content_bytes, mimetype=mime_type)
    sent = email.send(fail_silently=False)
    return {"sent": bool(sent), "via": "django-backend"}

def send_email(
    to: List[str],
    subject: str,
    text: str,
    html: Optional[str] = None,
    attachments: Optional[List[Tuple[str, bytes, str]]] = None,
) -> dict:
    # Forced provider selection logic
    if EMAIL_PROVIDER == 'django':
        return _send_via_django(to, subject, text, attachments)
    if EMAIL_PROVIDER == 'sendgrid':
        if sendgrid_available():
            sg = send_sendgrid_message(to=to, subject=subject, text=text, html=html, attachments=attachments)
            if sg.get('sent') or FORCE_DISABLE_SENDGRID:
                return sg
        # If forced sendgrid but unavailable, fall back to django to avoid silent failure.
        return _send_via_django(to, subject, text, attachments)

    # Default adaptive flow
    if not FORCE_DISABLE_SENDGRID and sendgrid_available():
        sg = send_sendgrid_message(to=to, subject=subject, text=text, html=html, attachments=attachments)
        if sg.get('sent'):
            return sg
    return _send_via_django(to, subject, text, attachments)

__all__ = ["send_email"]
