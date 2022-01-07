#!/usr/bin/env bash

# First try: copy wholesale
# copy data: copy data from all tables except {}
# docker-compose exec pgloader pgloader --with "prefetch rows = 1000" mysql://root:password@mysqldb/perma postgresql://postgres:password@db/postgres

# Second try: init db from Django migrations, copy over data
docker-compose exec web pipenv run ./manage.py migrate --noinput
docker-compose exec db PGPASSWORD=password psql -U perma -d perma -p password -c 'ALTER SCHEMA public RENAME TO perma'
docker-compose exec pgloader pgloader --with "prefetch rows = 1000" --with "create no tables" --with "include no drop" --with "truncate" mysql://root:password@mysqldb/perma postgresql://perma:password@db/perma
docker-compose exec db psql -U perma -d perma -p password -c 'ALTER SCHEMA perma RENAME TO public'
