FROM registry.lil.tools/library/debian:bullseye
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_SRC=/usr/local/src \
    PIPENV_HIDE_EMOJIS=true \
    PIPENV_NOSPIN=true \
    OPENSSL_CONF=/etc/ssl
RUN mkdir -p /perma/perma_web
WORKDIR /perma/perma_web

# Get build dependencies and packages required by the app
RUN apt-get update \
    && apt-get install -y wget \
    && apt-get install -y curl \
    && apt-get install -y bzip2 \
    && apt-get install -y gnupg \
    && apt-get install -y python3-pip \
    && apt-get install -y python3-dev \
    && apt-get install -y virtualenv \
    && apt-get install -y git \
    \
    && apt-get install -y postgresql-client \
    && apt-get install -y libpq-dev \
    && apt-get install -y xvfb \
    && apt-get install -y libffi-dev \
    && apt-get install -y libjpeg62-turbo-dev \
    && apt-get install -y libfontconfig1 \
    && apt-get install -y imagemagick \
    && apt-get install -y libmagickwand-dev

# Install commonly used web fonts for better screen shots.
RUN echo "deb http://deb.debian.org/debian bullseye main contrib" > /etc/apt/sources.list \
    && echo "deb https://deb.debian.org/debian-security bullseye-security main contrib" >> /etc/apt/sources.list \
    && echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections \
    && apt-get update \
    && apt-get install -y ttf-mscorefonts-installer \
    && apt-get install -y fonts-roboto

# Install a cert for use by warcprox
COPY services/warcprox/perma-warcprox-ca.pem /perma/perma_web
RUN apt-get update && apt-get install -y libnss3-tools \
    && mkdir -p $HOME/.pki/nssdb \
    && certutil -d $HOME/.pki/nssdb -N --empty-password \
    && certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n 'warcprox CA cert' -i perma-warcprox-ca.pem

# Install Tor, for optional use as a proxy
RUN apt-get update && apt-get install -y tor

# pin node version -- see https://github.com/nodesource/distributions/issues/33
ARG BUILDARCH
ENV BUILDARCH=${BUILDARCH:-amd64}
RUN curl -o nodejs.deb https://deb.nodesource.com/node_14.x/pool/main/n/nodejs/nodejs_14.19.0-deb-1nodesource1_${BUILDARCH}.deb \
    && dpkg -i ./nodejs.deb \
    && rm nodejs.deb

# npm
COPY perma_web/package.json /perma/perma_web
COPY perma_web/npm-shrinkwrap.json /perma/perma_web
RUN npm install \
    && rm package.json \
    && rm npm-shrinkwrap.json

# python requirements via pipenv.
# to access the virtualenv, invoke python like this: `pipenv run python`
# COPY Pipfile though it is ignored, per https://github.com/pypa/pipenv/issues/2834
COPY perma_web/Pipfile /perma/perma_web
COPY perma_web/Pipfile.lock /perma/perma_web
RUN pip3 install -U pip \
    && pip install pipenv \
    && pipenv --python 3.9 install --ignore-pipfile --dev \
    && rm Pipfile.lock

# Install Chrome
# technique from https://github.com/SeleniumHQ/docker-selenium/blob/master/NodeChrome/Dockerfile.txt
# ARG chrome-layer-cache-buster
# RUN apt-get --allow-releaseinfo-change update \
#     && apt-get install -y unzip libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libgbm1 libgtk-3-0 libnspr4 libnss3 libxcomposite1 libxcursor1 libxi6 libxrandr2 libxss1 libxtst6 xdg-utils \
#     && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
#     && dpkg -i google-chrome*.deb \
#     && CHROME_MAJOR_VERSION=$(google-chrome --version | sed -E "s/.* ([0-9]+)(\.[0-9]+){3}.*/\1/") \
#     && CHROME_DRIVER_VERSION=$(wget --no-verbose -O - "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}") \
#     && wget https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
#     && unzip chromedriver_linux64.zip \
#     && mv chromedriver /usr/bin/chromedriver \
#     && chmod +x /usr/bin/chromedriver

# Install Chromium dependencies
RUN apt-get install -y unzip libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libgbm1 libgtk-3-0 libnspr4 libnss3 libxcomposite1 libxcursor1 libxi6 libxrandr2 libxss1 libxtst6 xdg-utils

# Install Chromium and driver
RUN export LOC="http://ports.ubuntu.com/pool/universe/c/chromium-browser" \
    && export VER="97.0.4692.71-0ubuntu0.18.04.1_${BUILDARCH}" \
    && wget ${LOC}/chromium-codecs-ffmpeg-extra_${VER}.deb \
    && wget ${LOC}/chromium-browser_${VER}.deb \
    && wget ${LOC}/chromium-chromedriver_${VER}.deb \
    && dpkg -i ./chromium-codecs-ffmpeg-extra_${VER}.deb \
    && dpkg -i ./chromium-browser_${VER}.deb \
    && dpkg -i ./chromium-chromedriver_${VER}.deb

# dev personalizations / try installing packages without rebuilding everything
# RUN apt-get update && apt-get install -y nano
