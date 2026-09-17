# One Dockerfile, five targets, in the shape of h2o's:
#
#   base    Python + node runtime and Perma's dependency set. No app code.
#   assets  The compiled webpack bundles, built from source in a node image.
#   prod    The deployable image: base + app code + bundles + uwsgi, non-root.
#           Every ECS role (web, migrate, beat, each worker) runs this image;
#           the container command chooses the role.
#   test    prod + the test toolchain. What CI runs the suite against.
#   dev     base + the test toolchain, no app code; docker-compose bind-mounts
#           the working tree at /perma.
#
# Layout inside the image mirrors the repository: /perma is the checkout,
# /perma/perma_web the Django project (WORKDIR), /perma/services the
# sidecar directories (js-wacz, cloudflare IP lists, the RDS CA bundle).

# =====================================================================
# base -- shared Python/node dependency layer. No app code. Not run directly.
# =====================================================================
FROM python:3.11-bookworm AS base

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /perma/perma_web

# Packages the app links against at runtime (libpq for psycopg2, libxml2/xslt
# for lxml via warctools), plus what every stage's tooling needs. certutil
# (libnss3-tools) is what the test suite uses to trust its mkcert certificates;
# it is small and stays here so dev and test agree.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        git \
        nano \
        procps \
        postgresql-client \
        libpq-dev \
        libffi-dev \
        libnss3-tools \
        libxml2-dev \
        libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# node.js, pinned. Needed in prod (not only test): the wacz-conversion worker
# shells out to `npx js-wacz` from /perma/services/js-wacz. Version tracks the
# `assets` stage below and Salt's warc-wacz state.
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
        | gpg --dearmor -o /usr/share/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" \
        > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs=20.13.0-1nodesource1 \
    && rm -rf /var/lib/apt/lists/*

# uv, pinned by image tag, for the locked Python install below and for the
# test stage's dev-group install.
COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /uvx /bin/

# js-wacz and its dependencies, for the wacz-conversion worker. Installed from
# the lockfile alone so this layer is independent of app-code changes.
COPY services/js-wacz/package.json services/js-wacz/package-lock.json /perma/services/js-wacz/
RUN npm ci --prefix /perma/services/js-wacz

# Python dependencies, locked. --no-dev keeps the test toolchain (pytest,
# playwright, factory-boy...) out of the runtime image; `test` and `dev` add
# it back. Only the lockfile inputs are copied so this expensive layer is
# shared by every target and survives app-code edits.
COPY perma_web/pyproject.toml perma_web/uv.lock ./
RUN uv sync --frozen --no-dev

# =====================================================================
# assets -- the compiled JS/CSS bundles. Built here rather than committed, so
# that `prod` and `test` come out of one build graph and cannot disagree about
# what the frontend is.
#
# Plain node image: this stage needs npm and nothing Python. Node version
# tracks `base`.
#
# WORKDIR matters here: webpack-bundle-tracker records absolute output paths
# in webpack-stats.json, and django-webpack-loader reads that file at runtime,
# so the bundles must be built at the path they are served from.
# =====================================================================
FROM node:20.13.0-bookworm AS assets

WORKDIR /perma/perma_web

# Dependencies first, so a frontend edit does not reinstall node_modules.
# npm-shrinkwrap.json is the lockfile; `npm ci` honours it.
COPY perma_web/package.json perma_web/npm-shrinkwrap.json ./
RUN npm ci

COPY perma_web/webpack.config.js ./
# static/ is an input as well as the output location: the SCSS resolves fonts,
# images and vendored CSS from static/ at build time, and the Vue sources live
# in static/frontend. static/bundles is written by the build below.
COPY perma_web/static ./static

RUN npm run build

# =====================================================================
# prod -- the deployable artifact. uwsgi, non-root user, app code baked in.
# =====================================================================
FROM base AS prod

# uwsgi is not in pyproject.toml (the Salt hosts take it from apt), so it is
# installed into the venv here, pinned. Build toolchain purged afterwards;
# the runtime needs only libpcre.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpcre3 \
        libpcre3-dev \
    && CPUCOUNT=1 uv pip install --no-cache uwsgi==2.0.31 \
    && apt-get purge -y --auto-remove build-essential libpcre3-dev \
    && rm -rf /var/lib/apt/lists/*

# Non-root user. HOME is real (-m) because the test stage, FROM here, needs
# an NSS certificate database under it.
RUN useradd -m -r perma && chown -R perma /perma

# The application: the Django project and the service directories the
# settings reference (SERVICES_DIR, CLOUDFLARE_DIR, JS_WACZ_DIR, and the RDS
# CA bundle settings_ecs names). services/js-wacz/node_modules came with
# `base`; the COPY below adds only the tracked files beside it.
COPY --chown=perma:perma perma_web/ ./
COPY --chown=perma:perma services/ /perma/services/
COPY --chown=perma:perma uwsgi.ini /perma/uwsgi.ini

# Overwrite whatever bundles the checkout happened to carry (none, once they
# are no longer committed) with the ones just built. This is what makes the
# shipped image self-contained.
COPY --from=assets --chown=perma:perma /perma/perma_web/static/bundles ./static/bundles
COPY --from=assets --chown=perma:perma /perma/perma_web/webpack-stats.json ./webpack-stats.json

# Select deployment settings at runtime via perma/settings/__init__.py
# (PERMA_SETTINGS_MODULE), instead of baking a settings.py into the image.
ENV PERMA_SETTINGS_MODULE=settings_ecs

# The short commit hash the Salt template computed at deploy time; here it is
# stamped at build time by CI (--build-arg PERMA_VERSION=<short sha>) and read
# by settings_ecs. It ends up in the datapackage.json of user uploads.
ARG PERMA_VERSION=dev
ENV PERMA_VERSION=$PERMA_VERSION

USER perma

# Two artifacts derived from INSTALLED_APPS, built here so they describe the
# image itself and can be read out of it without running it. The deploy
# sequence reads both, and CI attaches both to the published image.
#
# collectstatic fills STATIC_ROOT -- /perma/perma_web/static-collected under
# settings_prod and everything derived from it -- with perma_web/static, the
# compiled bundles, and the files that come from installed packages (admin,
# rest_framework, django_json_widget...). WhiteNoise serves it from there; the
# deploy publishes the same tree to the static bucket.
#
# migrations.json records the migration graph as it exists here, third-party
# migrations from site-packages included. perma/management/commands/
# migration_manifest.py documents the format.
#
# Both run as perma rather than root, so a container -- which runs as perma
# too -- can rewrite what they produced. They run under settings_build
# because settings_ecs, the runtime default set above, reads APP_CONFIG,
# which exists only in a deployed task.
RUN PERMA_SETTINGS_MODULE=settings_build python manage.py collectstatic --noinput \
    && PERMA_SETTINGS_MODULE=settings_build python manage.py migration_manifest --output ./migrations.json

EXPOSE 8000

# The web role. Workers, beat and the migrate task override this with the
# commands listed in the ECS task definitions. --die-on-term is set in the
# ini: without it uwsgi treats SIGTERM as "reload" and ECS has to kill it.
CMD ["uwsgi", "--ini", "/perma/uwsgi.ini"]

# =====================================================================
# dev -- local development. The test toolchain on top of `base`, with no app
# code: docker-compose bind-mounts the working tree at /perma so a developer
# edits and reruns without rebuilding. Runs as root, as the dev image always
# has, so bind-mounted files keep their host ownership semantics.
# =====================================================================
FROM base AS dev

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# The dev dependency group, on top of base's runtime set.
RUN uv sync --frozen

COPY docker/install-test-toolchain.sh /tmp/install-test-toolchain.sh
RUN /tmp/install-test-toolchain.sh && rm /tmp/install-test-toolchain.sh

# =====================================================================
# test -- what CI runs the suite against. FROM prod, so it carries prod's
# uwsgi layer, prod's non-root user and prod's baked-in code, plus the same
# toolchain `dev` gets. Tests therefore exercise the artifact that ships
# rather than a sibling of it.
#
# The toolchain must be installed as root, but the stage ends as `perma`
# again so the suite runs under prod's real permissions -- if the app can't
# write somewhere in production, CI finds out here.
# =====================================================================
FROM prod AS test

USER root

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# The dev dependency group, into the same venv prod uses.
RUN uv sync --frozen && chown -R perma /opt/venv

COPY docker/install-test-toolchain.sh /tmp/install-test-toolchain.sh
RUN /tmp/install-test-toolchain.sh && rm /tmp/install-test-toolchain.sh

# karma (npm test) needs node_modules, which prod has no business carrying.
# Taken from the assets stage rather than reinstalled, so the JS tests run
# against the very tree the bundles were built from.
COPY --from=assets --chown=perma:perma /perma/perma_web/node_modules ./node_modules

# The bundles are already baked in by the prod stage, and there are no npm
# sources here to rebuild them from, so the freshness check must not fire.
ENV PERMA_SKIP_ASSET_CHECK=1

# conftest.py adds the suite's mkcert certificates to an NSS database under
# $HOME, which has to exist for the user running the tests.
USER perma
RUN mkdir -p /home/perma/.pki/nssdb && certutil -d sql:/home/perma/.pki/nssdb -N --empty-password
