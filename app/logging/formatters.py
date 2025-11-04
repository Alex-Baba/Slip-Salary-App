import logging
import json


class SafeRequestFormatter(logging.Formatter):
    """A small formatter that ensures `record.request_log` exists.

    Some modules may emit records to the 'request' logger without the
    middleware-provided `extra={'request_log': ...}`. The default
    '%' formatter will raise or output 'None'. This formatter ensures
    the attribute exists and is a JSON string so the handler always
    writes a valid line.
    """

    def format(self, record):
        if not hasattr(record, 'request_log'):
            # Provide a minimal JSON placeholder so handlers have something
            record.request_log = json.dumps({'missing_request_log': True})
        return super().format(record)
