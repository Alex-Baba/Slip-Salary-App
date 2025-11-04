from django.core.management.base import BaseCommand
import logging
import json


class Command(BaseCommand):
    help = 'Emit a couple of test log lines to the request and send loggers.'

    def handle(self, *args, **options):
        req_logger = logging.getLogger('request')
        send_logger = logging.getLogger('send')

        # For the 'request' logger we must provide the `request_log` extra
        payload = {
            'method': 'TEST',
            'path': '/__log_test__',
            'remote_addr': '127.0.0.1',
            'user_id': None,
            'user_email': None,
            'owner_id': None,
            'idempotency_key': None,
            'req_len': 0,
            'body_preview': None,
            'status': 200,
            'duration_ms': 1,
            'outcome': 'success',
        }

        req_logger.info('log-test', extra={'request_log': json.dumps(payload)})
        send_logger.info('log-test send: %s', json.dumps({'ok': True}))
        self.stdout.write('wrote test logs')
