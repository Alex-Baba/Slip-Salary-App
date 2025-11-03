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
        idempotency_key = request.headers.get('Idempotency-Key') or request.headers.get('IDEMPOTENCY_KEY')
        status_code = getattr(response, 'status_code', None)
        outcome = 'success' if status_code and status_code < 400 else 'failure'

        msg = {
            'method': request.method,
            'path': request.get_full_path(),
            'remote_addr': request.META.get('REMOTE_ADDR'),
            'user_id': user_id,
            'user_email': user_email,
            'idempotency_key': idempotency_key,
            'req_len': getattr(request, '_rl_content_length', None),
            'body_preview': getattr(request, '_rl_body_preview', None),
            'status': status_code,
            'duration_ms': duration_ms,
            'outcome': outcome,
        }

        # Structured log with useful fields in 'extra' for log handlers
        logger.info("request %s %s %s %sms %s", msg['method'], msg['path'], msg['status'], msg['duration_ms'], msg['idempotency_key'], extra={'request_log': msg})
        return response
