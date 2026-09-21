# One Dockerfile, five targets, in the shape of h2o's:
#
#   base    Python + node runtime and Perma's dependency set. No app code.
#   assets  The compiled webpack bundles, built from source in a node image.
#   prod    The deployable image: base + app code + bundles + gunicorn, non-root.
#           Every ECS role (web, beat, each worker) runs this image;
#           the container command chooses the role.
#   test    prod + the test toolchain. What CI runs the suite against.
#   dev     base + the test toolchain, no app code; docker-compose bind-mounts
#           the working tree at /perma.
#
# Layout inside the image mirrors the repository: /perma is the checkout,
# /perma/perma_web the Django project (WORKDIR), /perma/services the
# sidecar directories (js-wacz, cloudflare IP lists, the RDS CA bundle).

# Pinned tool images, named once so every stage below agrees on them. uv is
# copied out of its image as a static binary; node is both the `assets`
# builder and the source of the Node runtime copied into `base`.
FROM ghcr.io/astral-sh/uv:0.12.7@sha256:95f2aa1fe59274951cfe9b0cbc7972e879ff1004bc8945d130a32eb0dbd85945 AS uv
FROM node:24.20.0-trixie-slim@sha256:50c3b2f6988dfc307b86e5301d69611af31f4789bdf232863b07d3b02fe55ae0 AS node

# =====================================================================
# base -- shared Python/node dependency layer. No app code. Not run directly.
# =====================================================================
FROM python:3.14-slim-trixie@sha256:cae66f2ef0ec51a9891263eeee7f987dacf0a9879e8aa9353d5606e0530619a5 AS base

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/perma/perma_web \
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
        build-essential \
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

# The wacz-conversion worker needs Node at runtime. Copy the same pinned
# runtime used to build the frontend; both stages use Debian trixie.
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

# uv, from the pinned stage above, for the locked Python install below and for
# the test stage's dev-group install.
COPY --from=uv /uv /uvx /bin/

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
# assets -- the compiled JS/CSS bundles. Built here rather than taken from the
# checkout's committed copies, so that `prod` and `test` come out of one build
# graph and cannot disagree about what the frontend is.
#
# Plain node image (the pinned `node` stage): this stage needs npm and nothing
# Python. Same node version as `base`.
#
# WORKDIR matters here: webpack-bundle-tracker records absolute output paths
# in webpack-stats.json, and django-webpack-loader reads that file at runtime,
# so the bundles must be built at the path they are served from.
# =====================================================================
FROM node AS assets

WORKDIR /perma/perma_web

# Dependencies first, so a frontend edit does not reinstall node_modules.
# npm-shrinkwrap.json is the lockfile; `npm ci` honours it.
COPY perma_web/package.json perma_web/npm-shrinkwrap.json perma_web/.npmrc ./
RUN npm ci

COPY perma_web/webpack.config.js perma_web/browserslist ./
# static/ is an input as well as the output location: the SCSS resolves fonts,
# images and vendored CSS from static/ at build time, and the Vue sources live
# in static/frontend. static/bundles is written by the build below.
COPY perma_web/static ./static

# Content-hashed bundle names; see webpack.config.js. The deploy publishes
# static/bundles to the static bucket as immutable.
RUN WEBPACK_CONTENT_HASH=1 npm run build

# =====================================================================
# prod -- the deployable artifact. gunicorn, non-root user, app code baked in.
# =====================================================================
FROM base AS prod

# gunicorn is in the locked dependency set `base` installed. (The Salt hosts
# run uWSGI from apt; uWSGI is end-of-life and the image does not carry it.)

# Non-root user. HOME is real (-m) because the test stage, FROM here, needs
# an NSS certificate database under it.
RUN useradd -m -r perma && chown -R perma /perma

# The application: the Django project and the service directories the
# settings reference (SERVICES_DIR, CLOUDFLARE_DIR, JS_WACZ_DIR, and the RDS
# CA bundle settings_ecs names). services/js-wacz/node_modules came with
# `base`; the COPY below adds only the tracked files beside it.
COPY --chown=perma:perma perma_web/ ./
COPY --chown=perma:perma services/ /perma/services/

# Add the bundles just built. The tracked copies the Salt hosts deploy from
# never reach this stage: .dockerignore excludes perma_web/static/bundles and
# webpack-stats.json from the build context, so the only bundles in the image
# are the ones the assets stage compiled. This is what makes the shipped image
# self-contained.
COPY --from=assets --chown=perma:perma /perma/perma_web/static/bundles ./static/bundles
COPY --from=assets --chown=perma:perma /perma/perma_web/webpack-stats.json ./webpack-stats.json

# Select deployment settings at runtime via perma/settings/__init__.py
# (PERMA_SETTINGS_MODULE), instead of baking a settings.py into the image.
ENV PERMA_SETTINGS_MODULE=settings_ecs

# The short commit hash the Salt template computed at deploy time
# (`private_source['revision'][:7]`); here it is stamped at build time and read
# by settings_ecs. It ends up in the datapackage.json of user uploads.
# Convention: the first seven characters of the commit SHA, i.e. CI passes
# `--build-arg PERMA_VERSION=${GITHUB_SHA::7}`, and passes the same value to
# the `test` build so that test's FROM-prod layers are the cached prod layers
# rather than a second copy stamped `dev`.
ARG PERMA_VERSION=dev
ENV PERMA_VERSION=$PERMA_VERSION

# DJANGO_SETTINGS_MODULE is deliberately not set here: manage.py, wsgi.py and
# celery.py default it to perma.settings themselves, and an image-level value
# would override pytest's settings_testing (pytest-django prefers the
# environment to pyproject.toml). The shared CI inspectors, which run
# `python -c` against this image without going through manage.py, pass
# `settings-module: perma.settings` instead.

USER perma

# collectstatic fills STATIC_ROOT -- /perma/perma_web/static-collected under
# settings_prod and everything derived from it -- with perma_web/static, the
# compiled bundles, and the files that come from installed packages (admin,
# rest_framework, django_json_widget...). WhiteNoise serves it from there; CI
# extracts the same tree from the image and publishes it as an artifact.
#
# Runs as perma rather than root, so a container -- which runs as perma too --
# can rewrite what it produced. It runs under settings_build because
# settings_ecs, the runtime default set above, reads APP_CONFIG, which exists
# only in a deployed task. Migration and Celery task inspection are done by
# shared CI tooling against this image under the same settings module, not
# baked in here.
RUN PERMA_SETTINGS_MODULE=settings_build python manage.py collectstatic --noinput

EXPOSE 8000

# The web role. Workers and beat override this with the commands listed in
# the ECS task definitions; migrations run by ECS Exec into the web task.
# Settings are in perma_web/gunicorn_config.py, beside manage.py.
CMD ["gunicorn", "--config", "gunicorn_config.py", "perma.wsgi:application"]

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
# gunicorn, prod's non-root user and prod's baked-in code, plus the same
# toolchain `dev` gets. Tests therefore exercise the artifact that ships
# rather than a sibling of it.
#
# The toolchain must be installed as root, but the stage ends as `perma`
# again so the suite runs under prod's real permissions -- if the app can't
# write somewhere in production, CI finds out here.
# =====================================================================
FROM prod AS test

# Inherited from prod as ENV; declared again so the build-arg is visibly part
# of this target's interface. Pass the same value as the prod build (see the
# prod stage) or the two builds stop sharing layers.
ARG PERMA_VERSION=dev

USER root

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# The dev dependency group, into the same venv prod uses. Everything prod
# carries is in the lockfile, so an exact sync removes nothing it ships.
RUN uv sync --frozen && chown -R perma /opt/venv

COPY docker/install-test-toolchain.sh /tmp/install-test-toolchain.sh
RUN /tmp/install-test-toolchain.sh && rm /tmp/install-test-toolchain.sh

# Vitest (npm test) needs node_modules, which prod has no business carrying.
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
