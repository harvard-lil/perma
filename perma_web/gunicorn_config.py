"""Production WSGI server for the ECS web role; override with GUNICORN_CMD_ARGS.

Follows h2o's web/gunicorn_config.py. The values that differ carry over what
the Salt hosts' uWSGI (repos/salt, perma.ini) ran with: five single-threaded
workers and a 90-second worker timeout.
"""

import json
import os

from lil_request_logging.gunicorn import AccessLogger


class PermaAccessLogger(AccessLogger):
    trusted_peers = ("127.0.0.1", "::1")

    def access(self, resp, req, environ, request_time):
        # Perma rewrites REMOTE_ADDR for Django. Trust the connection peer,
        # not the resulting client address, when logging proxy headers.
        super().access(resp, req, {**environ, "REMOTE_ADDR": req.peer_addr[0]},
                       request_time)


logger_class = PermaAccessLogger
raw_env = [
    "SERVICE_NAME=perma",
    f"ENVIRONMENT={json.loads(os.getenv('APP_CONFIG', '{}')).get('TIER', 'dev')}",
    # settings_ecs makes this the Postgres statement_timeout for the web
    # workers' connections. It is below `timeout` so that Postgres cancels a
    # long statement before the worker is killed; a killed worker's query
    # otherwise runs on with no client. It is set here, not from PERMA_ROLE,
    # because migrations and other manage.py commands run by ECS Exec in the
    # web container share its environment and must not inherit the limit.
    "PERMA_STATEMENT_TIMEOUT=60s",
]


# Only the cloudflared sidecar reaches this, over localhost.
bind = "0.0.0.0:8000"
# A sync worker accepts another connection only after finishing its request.
# gthread with one thread accepted and queued healthchecks behind slow requests,
# even while other workers were free. Sync also avoids starting interpreter
# shutdown while an in-flight request still needs boto3's thread pool.
worker_class = "sync"
workers = int(os.environ.get("WEB_CONCURRENCY", "5"))
threads = 1
# Sync intentionally closes origin connections; cloudflared reconnects over
# localhost. Browser-to-Cloudflare connection reuse is independent of this.
backlog = 1000

# Sync workers stop heartbeating while handling a request, so timeout bounds a
# stuck worker (unlike gthread's heartbeat-only timeout). Allow a little timer
# granularity; this is not an exact application-level deadline.
timeout = 90
# Paired with the ECS web container's 120-second stopTimeout. Permit a normal
# request to finish after SIGTERM before the master forcibly stops its worker.
graceful_timeout = 110
# Keep periodic recycling, but reduce process churn and spread restarts across
# workers. Recycle only after the current request has completed.
max_requests = 2000
max_requests_jitter = 500
worker_tmp_dir = "/dev/shm"

# The shared adapter writes JSON to stdout; Django application logs remain
# separate. Older ECS access-logformat overrides do not affect this adapter.
accesslog = "-"
errorlog = "-"
capture_output = True
# ECS owns process lifecycle; no separate administrative socket is needed.
control_socket_disable = True
# No upstream component needs to override WSGI routing via HTTP headers.
# X-Forwarded-For is handled by perma/wsgi.py's TRUSTED_PROXIES middleware.
forwarder_headers = ""
