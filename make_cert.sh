#!/usr/bin/env bash

# Put the mkcert rootCA.pem file somewhere easily shareable with the `web` container,
# so that we can install it before running end-to-end tests, which require a trusted
# secure context ("ignore_https_errors" is insufficient)
cp "$(mkcert -CAROOT)/rootCA.pem" perma_web/rootCA.pem

# Generate certs
HOSTS=$(docker compose run -T web bash -c "echo \"from django.conf import settings; print(' '.join(host for host in settings.ALLOWED_HOSTS))\" | python ./manage.py shell")
mkcert -key-file perma_web/perma-test.key -cert-file perma_web/perma-test.crt $HOSTS
mkcert -key-file services/docker/webrecorder/nginx/ssl/perma-archives.key -cert-file services/docker/webrecorder/nginx/ssl/perma-archives.crt perma-archives.test
mkcert -key-file services/docker/minio/ssl/private.key -cert-file services/docker/minio/ssl/public.crt perma.minio.test

# For end-to-end testing, arrange for the `web` container` to trust the certificates
docker compose exec web bash -c 'certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "mkcert root" -i rootCA.pem'
docker compose exec web bash -c 'certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "perma certs" -i perma-test.crt'
docker compose exec web bash -c 'certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "minio cert" -i /tmp/minio_ssl/public.crt'

# For dev convenience: restart minio and nginx (which will have crashed immediately) now that the required cert and key files are available
# (will be a no-op if the services weren't started in the first place, i.e., if docker compose isn't currently running `up`)
docker compose restart nginx
docker compose restart minio
