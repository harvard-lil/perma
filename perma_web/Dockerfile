FROM python:2-stretch
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /perma/perma_web
WORKDIR /perma/perma_web


# PhantomJS
RUN wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2 \
    && tar xvjf phantomjs-2.1.1-linux-x86_64.tar.bz2 \
    && mv phantomjs-2.1.1-linux-x86_64 /usr/local/share \
    && ln -sf /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/bin \
    && rm phantomjs-2.1.1-linux-x86_64.tar.bz2


# Get Node 6 instead of version in APT repository.
# Downloads an installation script, which ends by running
# apt-get update: no need to re-run at this layer
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash - \
    && apt-get install -y nodejs


# Get other dependencies.
RUN apt-get update \
    && apt-get install -y xvfb \
    && apt-get install -y mysql-client \
    && apt-get install -y nano


# npm
COPY package.json /perma/perma_web
COPY npm-shrinkwrap.json /perma/perma_web
RUN npm install \
    && rm package.json \
    && rm npm-shrinkwrap.json


# pip
COPY requirements.txt /perma/perma_web
RUN pip install -U pip \
    &&  pip install -r requirements.txt --src /usr/local/src \
    && rm requirements.txt
