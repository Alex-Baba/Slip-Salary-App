import os
from typing import List, Optional, Tuple
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, Header
import base64

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL', os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@example.com'))

def sendgrid_available() -> bool:
    return bool(SENDGRID_API_KEY)

def send_sendgrid_message(
    to: List[str],
    subject: str,
    text: str,
    html: Optional[str] = None,
    attachments: Optional[List[Tuple[str, bytes, str]]] = None,
) -> dict:
    if not sendgrid_available():
        return {"sent": False, "error": "SendGrid not configured"}
    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=to,
        subject=subject,
        plain_text_content=text,
        html_content=html if html else None,
    )
    # Add helpful categorization & headers for allowlisting.
    try:
        message.category = ["payroll", "payslip" if 'payslip' in subject.lower() else 'report']
    except Exception:
        pass
    # Custom headers that corporate filters can allowlist.
    try:
        message.add_header(Header("X-Payroll-App", "SlipSalaryV1"))
        message.add_header(Header("X-Transactional-Type", "compensation"))
    except Exception:
        pass
    # Optional reply-to (can be configured via env)
    reply_to = os.getenv('EMAIL_REPLY_TO')
    if reply_to:
        try:
            message.reply_to = reply_to
        except Exception:
            pass
    if attachments:
        for (filename, content_bytes, mime_type) in attachments:
            b64 = base64.b64encode(content_bytes).decode()
            attachment = Attachment(
                FileContent(b64),
                FileName(filename),
                FileType(mime_type),
                Disposition('attachment')
            )
            message.add_attachment(attachment)
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return {
            "sent": 200 <= response.status_code < 300,
            "status_code": response.status_code,
            "body": getattr(response, 'body', None),
            "headers": dict(getattr(response, 'headers', {})),
            "via": "sendgrid"
        }
    except Exception as e:
        return {"sent": False, "error": str(e), "via": "sendgrid"}

__all__ = ["send_sendgrid_message", "sendgrid_available"]
