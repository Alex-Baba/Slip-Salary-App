import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('request')


class RequestLoggingMiddleware(MiddlewareMixin):
    """Logs basic info for every HTTP request and response.

    Logs method, path, querystring, remote addr, user id (if available),
    request content length, response status code and duration in ms.
    """

    def process_request(self, request):
        request._rl_start_time = time.time()
        # Avoid logging full bodies; log length only
        try:
            request._rl_content_length = int(request.META.get('CONTENT_LENGTH') or 0)
        except Exception:
            request._rl_content_length = 0

    def process_response(self, request, response):
        start = getattr(request, '_rl_start_time', None)
        duration_ms = int((time.time() - start) * 1000) if start else None
        user_id = getattr(getattr(request, 'user', None), 'id', None)

        msg = {
            'method': request.method,
            'path': request.get_full_path(),
            'remote_addr': request.META.get('REMOTE_ADDR'),
            'user_id': user_id,
            'req_len': getattr(request, '_rl_content_length', None),
            'status': getattr(response, 'status_code', None),
            'duration_ms': duration_ms,
        }

        logger.info("request %s %s %s %sms", msg['method'], msg['path'], msg['status'], msg['duration_ms'], extra={'request_log': msg})
        return response
