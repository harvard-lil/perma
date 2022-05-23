#!/usr/bin/env bash

HOSTS=$(docker compose run -T web bash -c "echo \"from django.conf import settings; print(' '.join(host for host in settings.ALLOWED_HOSTS))\" | python ./manage.py shell")
mkcert -key-file perma_web/perma-test.key -cert-file perma_web/perma-test.crt $HOSTS
mkcert -key-file services/docker/webrecorder/nginx/ssl/perma-archives.key -cert-file services/docker/webrecorder/nginx/ssl/perma-archives.crt perma-archives.test
mkcert -key-file services/docker/minio/ssl/private.key -cert-file services/docker/minio/ssl/public.crt perma.minio.test

# For dev convenience: restart minio and nginx (which will have crashed immediately) now that the required cert and key files are available
# (will be a no-op if the services weren't started in the first place, i.e., if docker compose isn't currently running `up`)
docker compose restart nginx
docker compose restart minio
