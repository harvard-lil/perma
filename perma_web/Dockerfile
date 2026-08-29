# Extract Playwright version from uv.lock prior to building main image
FROM python:3.14-slim-trixie@sha256:cae66f2ef0ec51a9891263eeee7f987dacf0a9879e8aa9353d5606e0530619a5 AS extract-playwright-version
COPY perma_web/uv.lock /tmp/uv.lock
RUN grep -A 1 '^name = "playwright"$' /tmp/uv.lock | grep version | cut -d'"' -f2 > /tmp/.playwright-version

# Main image
FROM python:3.14-slim-trixie@sha256:cae66f2ef0ec51a9891263eeee7f987dacf0a9879e8aa9353d5606e0530619a5
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_SRC=/usr/local/src \
    OPENSSL_CONF=/etc/ssl \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
RUN mkdir -p /perma/perma_web
WORKDIR /perma/perma_web

# ttf-mscorefonts-installer is distributed through Debian contrib.
RUN sed -i 's/^Components: main$/Components: main contrib/' /etc/apt/sources.list.d/debian.sources \
    && echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections

# Get build dependencies and packages required by the app
RUN apt-get update \
    && apt-get install -y \
        wget \
        curl \
        bzip2 \
        build-essential \
        gnupg \
        python3-pip \
        python3-dev \
        python-is-python3 \
        virtualenv \
        git \
        nano \
        procps `# ps and pkill` \
        \
        postgresql-client \
        libpq-dev \
        libffi-dev \
        libnss3-tools                           `# for certutil` \
        libxml2-dev \
        libxslt-dev

# node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs=20.13.0-1nodesource1

# uv package manager
COPY --from=ghcr.io/astral-sh/uv:0.12.7@sha256:95f2aa1fe59274951cfe9b0cbc7972e879ff1004bc8945d130a32eb0dbd85945 /uv /uvx /bin/

# Copy Playwright version extracted in first stage
COPY --from=extract-playwright-version /tmp/.playwright-version /tmp/.playwright-version

# Install Playwright browsers for integration tests
RUN  apt-get update && apt install -y --no-install-recommends libdbus-glib-1-2 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatspi2.0-0 \
    libwayland-client0 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-xcb1 \
    libxcursor1 \
    libgtk-3-0 \
    libpangocairo-1.0-0 \
    libcairo-gobject2 \
    libgdk-pixbuf-2.0-0

RUN mkdir -p $HOME/.pki/nssdb \
    && certutil -d $HOME/.pki/nssdb -N --empty-password \
    && uvx playwright@$(cat /tmp/.playwright-version) install chromium firefox \
    && ln -sf "$(find /root/.cache/ms-playwright -name 'chrome' -type f -executable | head -1)" /usr/local/bin/playwright-chromium

# Frontend requirements
COPY perma_web/package.json /perma/perma_web
COPY perma_web/npm-shrinkwrap.json /perma/perma_web
RUN npm install \
    && rm package.json \
    && rm npm-shrinkwrap.json

# Worker requirements
COPY services/js-wacz/package.json /perma/services/js-wacz/package.json
COPY services/js-wacz/package-lock.json /perma/services/js-wacz/package-lock.json
RUN npm install --prefix /perma/services/js-wacz/ \
    && rm /perma/services/js-wacz/package.json \
    && rm /perma/services/js-wacz/package-lock.json

# Python requirements
COPY perma_web/pyproject.toml perma_web/uv.lock /perma/perma_web/
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
RUN uv sync --frozen
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/perma/perma_web"
