FROM mcr.microsoft.com/playwright:v1.18.1-focal

RUN apt-get update \
    && apt-get install -y python3.8 python3-pip \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1 \

    && apt-get install -y python3-dev \
    && apt-get install -y virtualenv

# Setup pseudo-home
RUN mkdir -p /playwright
WORKDIR /playwright

COPY playwright/Pipfile /playwright/Pipfile
COPY playwright/Pipfile.lock /playwright/Pipfile.lock
RUN pip3 install -U pip \
    && pip install pipenv \
    && pipenv --python 3.8 install --ignore-pipfile
