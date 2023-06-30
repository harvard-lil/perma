#!/usr/bin/env bash

# Put the mkcert rootCA.pem file somewhere easily shareable with the `web` container,
# so that we can install it before running end-to-end tests, which require a trusted
# secure context ("ignore_https_errors" is insufficient)
cp "$(mkcert -CAROOT)/rootCA.pem" perma_web/rootCA.pem

# Generate certs
mkcert -key-file perma_web/perma-test.key -cert-file perma_web/perma-test.crt perma.test api.perma.test
mkcert -key-file services/docker/minio/ssl/private.key -cert-file services/docker/minio/ssl/public.crt perma.minio.test
mkcert -key-file services/docker/wacz-exhibitor/ssl/private.key -cert-file services/docker/wacz-exhibitor/ssl/public.crt rejouer.perma.test

# For dev convenience: restart minio and wacz-exhibitor (which will have crashed immediately) now that the required cert and key files are available
# (will be a no-op if the services weren't started in the first place, i.e., if docker compose isn't currently running `up`)
docker compose restart minio
docker compose restart wacz-exhibitor
