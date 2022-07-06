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
        xvfb \
        libffi-dev \
        libjpeg62-turbo-dev \
        libfontconfig1 \
        imagemagick \
        libmagickwand-dev \
        ttf-mscorefonts-installer fonts-roboto  `# commonly used web fonts for better screen shots` \
        libnss3-tools                           `# for certutil` \
        tor                                     `# for optional use as a proxy`

# Install a cert for use by warcprox
COPY perma_web/perma-warcprox-ca.pem /perma/perma_web
RUN mkdir -p $HOME/.pki/nssdb \
    && certutil -d $HOME/.pki/nssdb -N --empty-password \
    && certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n 'warcprox CA cert' -i perma-warcprox-ca.pem

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

# Install Chromium and driver
COPY perma_web/lil-archive-keyring.gpg /usr/share/keyrings/lil-archive-keyring.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/lil-archive-keyring.gpg] https://repo.lil.tools/ bullseye-security updates/main" > /etc/apt/sources.list.d/lil-chromium.list

ENV CHROMIUM_VERSION=103.0.5060.53-1~deb11u1
RUN apt-get update && apt-get install -y chromium=${CHROMIUM_VERSION} \
    chromium-common=${CHROMIUM_VERSION} \
    chromium-driver=${CHROMIUM_VERSION} \
    chromium-l10n=${CHROMIUM_VERSION} \
    chromium-sandbox=${CHROMIUM_VERSION}
