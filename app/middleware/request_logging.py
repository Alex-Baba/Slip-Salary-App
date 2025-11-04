import time
import logging
import json
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('request')


class RequestLoggingMiddleware(MiddlewareMixin):
    """Logs basic info for every HTTP request and response.

    Includes: method, path, querystring, remote addr, user id/email (if available),
    Idempotency-Key header, small request body summary (JSON keys or truncated body),
    response status code, duration in ms and an outcome label (success/failure).
    """

    def process_request(self, request):
        request._rl_start_time = time.time()
        # Avoid logging full bodies; log length only and a tiny preview
        try:
            request._rl_content_length = int(request.META.get('CONTENT_LENGTH') or 0)
        except Exception:
            request._rl_content_length = 0
        # small body preview: attempt to parse JSON and keep keys, otherwise raw trunc
        try:
            if request._rl_content_length and request.body:
                content = request.body.decode('utf-8', errors='ignore')
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        request._rl_body_preview = {'keys': list(parsed.keys())}
                    else:
                        request._rl_body_preview = str(parsed)[:256]
                except Exception:
                    request._rl_body_preview = content[:256]
            else:
                request._rl_body_preview = None
        except Exception:
            request._rl_body_preview = None

    def process_response(self, request, response):
        start = getattr(request, '_rl_start_time', None)
        duration_ms = int((time.time() - start) * 1000) if start else None
        user = getattr(request, 'user', None)
        user_id = getattr(user, 'id', None)
        user_email = getattr(user, 'email', None)
        # Try to resolve application-level employee (owner) if available; do this lazily
        owner_id = None
        actor = None
        try:
            # import here to avoid import-time side-effects
            from app.services.auth_utils import get_current_employee
            try:
                actor = get_current_employee(request)
                owner_id = getattr(actor, 'id', None)
            except Exception:
                actor = None
                owner_id = None
        except Exception:
            actor = None
            owner_id = None

        # If Django's AuthenticationMiddleware didn't populate request.user (common with
        # custom JWT handling), fall back to the application-level actor so logs are
        # more useful and avoid nulls for user_id/user_email.
        # Use explicit None checks to avoid skipping assignment when user_id is falsy.
        if user_id is None and owner_id is not None:
            user_id = owner_id
        if (user_email is None or user_email == '') and actor is not None:
            user_email = getattr(actor, 'email', None)
        idempotency_key = request.headers.get('Idempotency-Key') or request.headers.get('IDEMPOTENCY_KEY')
        status_code = getattr(response, 'status_code', None)
        outcome = 'success' if status_code and status_code < 400 else 'failure'

        msg = {
            'method': request.method,
            'path': request.get_full_path(),
            'remote_addr': request.META.get('REMOTE_ADDR'),
            'user_id': user_id,
            'user_email': user_email,
            'owner_id': owner_id,
            'idempotency_key': idempotency_key,
            'req_len': getattr(request, '_rl_content_length', None),
            'body_preview': getattr(request, '_rl_body_preview', None),
            'status': status_code,
            'duration_ms': duration_ms,
            'outcome': outcome,
        }
        # Structured log: put a JSON string in extra so formatters can render it reliably
        request_log_json = json.dumps(msg, default=str)
        logger.info("request %s %s %s %sms %s | %s", msg['method'], msg['path'], msg['status'], msg['duration_ms'], msg['idempotency_key'], json.dumps({'owner_id': owner_id}), extra={'request_log': request_log_json})
        return response
