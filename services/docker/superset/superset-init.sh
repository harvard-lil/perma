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

# create perma db connection if it doesn't exist
superset set-database-uri -d "$DATABASE_NAME" -u "$SQLALCHEMY_URI" -s

# start server
/bin/sh -c /usr/bin/run-server.sh
