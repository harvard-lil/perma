FROM registry.lil.tools/library/debian:11.3
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_SRC=/usr/local/src \
    OPENSSL_CONF=/etc/ssl
RUN mkdir -p /perma/perma_web
WORKDIR /perma/perma_web

# For fonts-roboto and ttf-mscorefonts-installer
RUN echo "deb http://deb.debian.org/debian bullseye main contrib" > /etc/apt/sources.list \
    && echo "deb https://deb.debian.org/debian-security bullseye-security main contrib" >> /etc/apt/sources.list \
    && echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections

# Get build dependencies and packages required by the app
RUN apt-get update \
    && apt-get install -y \
        wget \
        curl \
        bzip2 \
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
        libnss3-tools                           `# for certutil`

# pin node version -- see https://github.com/nodesource/distributions/issues/33
RUN curl -o nodejs.deb https://deb.nodesource.com/node_14.x/pool/main/n/nodejs/nodejs_14.19.3-deb-1nodesource1_$(dpkg --print-architecture).deb \
    && dpkg -i ./nodejs.deb \
    && rm nodejs.deb

# npm
COPY perma_web/package.json /perma/perma_web
COPY perma_web/npm-shrinkwrap.json /perma/perma_web
RUN npm install \
    && rm package.json \
    && rm npm-shrinkwrap.json

# python requirements
COPY perma_web/requirements.txt /perma/perma_web
RUN pip install pip==22.0.4 \
    && pip install -r /perma/perma_web/requirements.txt \
    && rm /perma/perma_web/requirements.txt

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
    libcairo2

RUN mkdir -p $HOME/.pki/nssdb \
    && certutil -d $HOME/.pki/nssdb -N --empty-password \
    && playwright install chromium firefox
