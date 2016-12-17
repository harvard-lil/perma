from opbeat.middleware import Opbeat
from opbeat.utils import disabled_due_to_debug

import perma.settings

opbeat_disabled = disabled_due_to_debug(
    getattr(perma.settings, 'OPBEAT', {}),
    perma.settings.DEBUG
)

class PywbOpbeatMiddleware(Opbeat):
    def __call__(self, environ, start_response):

        start_response_args = {}
        try:
            if not opbeat_disabled:
                self.client.begin_transaction("web.pywb")

            def start_response_wrapper(status, response_headers, exc_info=None):
                start_response_args['status'] = status
                start_response_args['response_headers'] = response_headers
                start_response_args['exc_info'] = exc_info
                return start_response(status, response_headers, exc_info)

            for event in self.application(environ, start_response_wrapper):
                yield event

        finally:
            try:
                if start_response_args:
                    status = int(start_response_args['status'].split(' ', 1)[0])
                    self.client.end_transaction("pywb", status)
            except Exception:
                self.client.error_logger.error('Exception during timing of request', exc_info=True, )
