import os
import requests
from typing import List, Optional

MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
MAILGUN_BASE_URL = os.getenv('MAILGUN_BASE_URL', 'https://api.mailgun.net/v3')

def mailgun_available() -> bool:
    return bool(MAILGUN_API_KEY and MAILGUN_DOMAIN)

def send_mailgun_message(
    to: List[str],
    subject: str,
    text: str,
    html: Optional[str] = None,
    attachments: Optional[List[tuple]] = None,
    from_email: Optional[str] = None,
) -> dict:
    """Send an email via Mailgun API.

    attachments: list of tuples (filename, bytes, mime_type)
    Returns dict with success flag and response status/code.
    """
    if not mailgun_available():
        return {"sent": False, "error": "Mailgun not configured"}

    from_email = from_email or f"Mailgun Sandbox <postmaster@{MAILGUN_DOMAIN}>"
    url = f"{MAILGUN_BASE_URL}/{MAILGUN_DOMAIN}/messages"
    data = {
        "from": from_email,
        "to": to,
        "subject": subject,
        "text": text,
    }
    if html:
        data["html"] = html

    files = []
    if attachments:
        for (filename, content, mime) in attachments:
            files.append(("attachment", (filename, content, mime)))

    key_prefix_valid = MAILGUN_API_KEY.startswith('key-') if MAILGUN_API_KEY else False
    try:
        resp = requests.post(
            url,
            auth=("api", MAILGUN_API_KEY),
            data=data,
            files=files if files else None,
            timeout=15
        )
        content_type = resp.headers.get('content-type', '')
        parsed = None
        if content_type.startswith('application/json'):
            try:
                parsed = resp.json()
            except Exception:
                parsed = {"raw": resp.text}
        else:
            parsed = {"raw": resp.text}
        ok = resp.status_code == 200
        result = {
            "sent": ok,
            "status_code": resp.status_code,
            "response": parsed,
            "domain": MAILGUN_DOMAIN,
            "base_url": MAILGUN_BASE_URL,
            "key_prefix_valid": key_prefix_valid,
        }
        if not ok:
            # Provide actionable hints
            hints = []
            if not key_prefix_valid:
                hints.append("API key does not start with 'key-' (likely using public or wrong key)")
            if MAILGUN_DOMAIN and MAILGUN_DOMAIN.startswith('sandbox'):
                hints.append("Ensure recipient is authorized for sandbox domain")
            if MAILGUN_BASE_URL.startswith('https://api.mailgun.net') and 'eu' in (MAILGUN_DOMAIN or ''):
                hints.append("EU domain may require base URL https://api.eu.mailgun.net/v3")
            if resp.status_code in (401, 403):
                hints.append("Authentication/permission issue: verify private key, domain spelling, and region")
            if hints:
                result['hints'] = hints
        return result
    except Exception as e:
        return {
            "sent": False,
            "error": str(e),
            "domain": MAILGUN_DOMAIN,
            "base_url": MAILGUN_BASE_URL,
            "key_prefix_valid": key_prefix_valid,
        }

__all__ = ["send_mailgun_message", "mailgun_available"]
