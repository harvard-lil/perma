#!/usr/bin/env bash

HOSTS=$(docker compose run -T web bash -c "echo \"from django.conf import settings; print(' '.join(host for host in settings.ALLOWED_HOSTS))\" | python ./manage.py shell")
mkcert -key-file perma_web/perma-test.key -cert-file perma_web/perma-test.crt $HOSTS
mkcert -key-file services/docker/webrecorder/nginx/ssl/perma-archives.key -cert-file services/docker/webrecorder/nginx/ssl/perma-archives.crt perma-archives.test

# For dev convenience: restart nginx (which will have crashed immediately) now that the required cert and key files are available
# (will be a no-op if the nginx servce wasn't started in the first place, i.e., if docker compose isn't currently running `up`)
docker compose restart nginx
