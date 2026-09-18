"""Production WSGI server for the ECS web role; override with GUNICORN_CMD_ARGS.

Follows h2o's web/gunicorn_config.py. The values that differ carry over what
the Salt hosts' uWSGI (repos/salt, perma.ini) ran with: five single-threaded
workers, a 90-second request limit, workers recycled every ~500 requests.
"""

import os

# Only the cloudflared sidecar reaches this, over localhost.
bind = "0.0.0.0:8000"
# gthread lets cloudflared reuse HTTP connections. One thread per worker keeps
# the concurrency model the Salt hosts had (uWSGI processes = 5, threads = 1);
# Perma has not run request handling threaded.
worker_class = "gthread"
workers = int(os.environ.get("WEB_CONCURRENCY", "5"))
threads = 1
keepalive = 5
backlog = 1000

# uWSGI's harakiri was 90 seconds.
timeout = 90
# ECS gives the container 30 seconds after SIGTERM (no stopTimeout is set on
# the web container); leave time for process cleanup. The cloudflared sidecar
# drains requests before ECS stops the app.
graceful_timeout = 25
max_requests = 500
max_requests_jitter = 10
worker_tmp_dir = "/dev/shm"

# Access logging stays off, as on the Salt hosts: Cloudflare keeps the access
# log. Application logging still reaches stdout through Django's LOGGING.
accesslog = None
errorlog = "-"
capture_output = True
# ECS owns process lifecycle; no separate administrative socket is needed.
control_socket_disable = True
# No upstream component needs to override WSGI routing via HTTP headers.
# X-Forwarded-For is handled by perma/wsgi.py's TRUSTED_PROXIES middleware.
forwarder_headers = ""
