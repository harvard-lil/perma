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
# commenting this out for now because the below import-dashboard cmd creates the db connection as well
# superset set-database-uri -d "$DATABASE_NAME" -u "$SQLALCHEMY_URI"

# import dashboard and their related data such as charts, datasets and database connection
superset import-dashboards \
        --path '/app/dashboard_export.zip' \
        --username "$ADMIN_USERNAME"

# start server
/bin/sh -c /usr/bin/run-server.sh
