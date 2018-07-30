FROM debian:stretch-20180426
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_SRC=/usr/local/src \
    PIPENV_HIDE_EMOJIS=true \
    PIPENV_NOSPIN=true
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
    && apt-get install -y mysql-client \
    && apt-get install -y default-libmysqlclient-dev \
    && apt-get install -y xvfb \
    && apt-get install -y libffi-dev \
    && apt-get install -y libjpeg62-turbo-dev \
    && apt-get install -y libfontconfig1 \
    && apt-get install -y imagemagick \
    && apt-get install -y libmagickwand-dev

# Install commonly used web fonts for better screen shots.
RUN echo "deb http://httpredir.debian.org/debian stretch main contrib" > /etc/apt/sources.list \
    && echo "deb http://security.debian.org/ stretch/updates main contrib" >> /etc/apt/sources.list \
    && echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections \
    && apt-get update \
    && apt-get install -y ttf-mscorefonts-installer \
    && apt-get install -y fonts-roboto

# PhantomJS
RUN wget https://s3.amazonaws.com/perma/phantomjs-2.1.1-linux-x86_64.tar.bz2 \
    && tar xvjf phantomjs-2.1.1-linux-x86_64.tar.bz2 \
    && mv phantomjs-2.1.1-linux-x86_64 /usr/local/share \
    && ln -sf /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/bin \
    && rm phantomjs-2.1.1-linux-x86_64.tar.bz2

# Get Node 6 instead of version in APT repository.
# Downloads an installation script, which ends by running
# apt-get update: no need to re-run at this layer
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash - \
    && apt-get install -y nodejs

# npm
COPY npm-shrinkwrap.json /perma/perma_web
RUN npm install \
    && rm npm-shrinkwrap.json

# Make a python3 virtualenv and install requirements there.
# The venv must be manually activated before running docker commands.... terrible
#RUN virtualenv -p /usr/bin/python3.5 /usr/local/share/.virtualenvs/perma \
#    && . /usr/local/share/.virtualenvs/perma/bin/activate \
#    && pip install -U "pip>=9,<10" \
#    && pip install -r requirements.txt \
#    && rm requirements.txt

# make python3 the system python... creepy
#RUN update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1 \
#    && update-alternatives --install /usr/bin/python python /usr/bin/python3.5 2
#COPY requirements.txt /perma/perma_web
#RUN pip3 install -U "pip>=9,<10" \
#    && pip install -r requirements.txt --src /usr/local/src \
#    && rm requirements.txt

# python requirements via pipenv.
# to access the virtualenv, invoke python like this: `pipenv run python`
COPY Pipfile.lock /perma/perma_web
RUN pip3 install -U "pip>=9,<10" \
    && pip install pipenv \
    && pipenv --python 3.5 install --ignore-pipfile\
    && rm Pipfile.lock

# dev personalizations / try installing packages without rebuilding everything
RUN apt-get install -y nano
