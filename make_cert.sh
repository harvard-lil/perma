#!/usr/bin/env bash

HOSTS=$(docker compose exec -T web bash -c "echo \"from django.conf import settings; print(' '.join(host for host in settings.ALLOWED_HOSTS))\" | python ./manage.py shell")
mkcert -key-file perma_web/perma-test.key -cert-file perma_web/perma-test.crt $HOSTS
mkcert -key-file services/docker/webrecorder/nginx/perma-archives.key -cert-file services/docker/webrecorder/nginx/perma-archives.crt perma-archives.test
