"""Production WSGI server for the ECS web role; override with GUNICORN_CMD_ARGS.

Follows h2o's web/gunicorn_config.py. The values that differ carry over what
the Salt hosts' uWSGI (repos/salt, perma.ini) ran with: five single-threaded
workers and a 90-second worker timeout.
"""

import os

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

# ECS supplies the combined access format, duration and Cloudflare request ID
# through GUNICORN_CMD_ARGS. Django application logs also go to stdout.
accesslog = None
errorlog = "-"
capture_output = True
# ECS owns process lifecycle; no separate administrative socket is needed.
control_socket_disable = True
# No upstream component needs to override WSGI routing via HTTP headers.
# X-Forwarded-For is handled by perma/wsgi.py's TRUSTED_PROXIES middleware.
forwarder_headers = ""
