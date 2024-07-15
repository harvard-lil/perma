#!/bin/bash

# create admin user
superset fab create-admin \
        --username "$ADMIN_USERNAME" \
        --firstname Superset \
        --lastname Admin \
        --email "$ADMIN_EMAIL" \
        --password "$ADMIN_PASSWORD"

# upgrade superset metastore
superset db upgrade

# set up roles and permissions
superset init

# create perma db connection
# the below import-dashboards cmd creates the db connection as well
# if you don't want to import the data objects but only create db connection, use this instead of import-dashboards
# superset set-database-uri -d "$DATABASE_NAME" -u "$SQLALCHEMY_URI"

# import dashboards and their related data such as charts, datasets and database connection
# it will override the existing dashboard that has the same name
superset import-dashboards \
        --path '/app/dashboard_export.zip' \
        --username "$ADMIN_USERNAME"

# start server
/bin/sh -c /usr/bin/run-server.sh
