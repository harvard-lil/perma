FROM dimitri/pgloader

# work around problem with stable-slim image (https://github.com/debuerreotype/docker-debian-artifacts/issues/137)
# https://serverfault.com/a/1074701
RUN sed -i 's/stable\/updates/stable-security\/updates/' /etc/apt/sources.list

RUN apt-get update \
    && apt-get install -y default-mysql-client \
    && apt-get install -y postgresql-client
