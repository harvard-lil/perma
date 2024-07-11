#!/bin/bash

# create admin user
superset fab create-admin --username admin --firstname Superset --lastname Admin --email admin@superset.com --password admin

# upgrade superset metastore
superset db upgrade

# set up roles and permissions
superset init

# start server
/bin/sh -c /usr/bin/run-server.sh
