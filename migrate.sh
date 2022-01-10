#!/usr/bin/env bash

# First try: copy wholesale
# copy data: copy data from all tables except {}
# docker-compose exec pgloader pgloader --with "prefetch rows = 1000" mysql://root:password@mysqldb/perma postgresql://postgres:password@db/postgres

# Second try: init db from Django migrations, copy over data
# docker-compose exec web pipenv run ./manage.py migrate --noinput
# docker-compose exec db bash -c "PGPASSWORD=password psql -U perma -d perma -c 'ALTER SCHEMA public RENAME TO perma'"
# docker-compose exec pgloader pgloader --with "prefetch rows = 1000" --with "create no tables" --with "include no drop" --with "truncate" mysql://root:password@mysqldb/perma postgresql://perma:password@db/perma
# docker-compose exec db bash -c "PGPASSWORD=password psql -U perma -d perma -c 'ALTER SCHEMA perma RENAME TO public'"

# Third try: init db from Django migrations, copy over data with "data only"
# docker-compose exec web pipenv run ./manage.py migrate --noinput
# docker-compose exec db bash -c "PGPASSWORD=password psql -U perma -d perma -c 'ALTER SCHEMA public RENAME TO perma'"
# docker-compose exec pgloader pgloader --with "prefetch rows = 1000" --with "data only" --with "truncate" mysql://root:password@mysqldb/perma postgresql://perma:password@db/perma
# docker-compose exec db bash -c "PGPASSWORD=password psql -U perma -d perma -c 'ALTER SCHEMA perma RENAME TO public'"

# Fourth try: configure pgloader with file for more control
docker-compose exec web pipenv run ./manage.py migrate --noinput
docker-compose exec db bash -c "PGPASSWORD=password psql -U perma -d perma -c 'ALTER SCHEMA public RENAME TO perma'"
docker-compose exec pgloader pgloader /tmp/perma.load
docker-compose exec db bash -c "PGPASSWORD=password psql -U perma -d perma -c 'ALTER SCHEMA perma RENAME TO public'"
