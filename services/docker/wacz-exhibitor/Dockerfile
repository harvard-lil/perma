# Local replay host for development and CI: wacz-exhibitor's static files,
# served by nginx with the TLS and proxy settings in nginx.conf.
FROM nginx:1.30.5@sha256:b972f831f200b19ef0767938224f9711e74cd783718738cd7405d5cabf75c442

# The wacz-exhibitor release, which fixes the ReplayWeb.page version.
# docker-compose.yml sets it; this default only serves a bare `docker build`.
ARG RELEASE=v0.2.18
ADD https://github.com/harvard-lil/wacz-exhibitor.git#${RELEASE}:html /usr/share/nginx/html/

COPY ./nginx.conf /etc/nginx/conf.d/nginx.conf
COPY ./replay-web-page-index.html /usr/share/nginx/html/replay-web-page/index.html
