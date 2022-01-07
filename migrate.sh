#!/usr/bin/env bash

# First try: copy wholesale
# copy data: copy data from all tables except {}
docker-compose exec pgloader pgloader --with "prefetch rows = 1000" mysql://root:password@mysqldb/perma postgresql://postgres:password@db/postgres

# Second try: init db from Django migrations, copy over data
#docker-compose exec web pipenv run ./manage.py migrate --noinput
