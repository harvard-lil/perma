#!/usr/bin/env bash

# This script rebuilds the Docker containers, installing a new version of
# Chromium if specified in the Dockerfile, and updates our user agent and
# image version number if necessary.

docker-compose up -d --build
LATEST=`docker-compose exec -T web bash -c "chromium --version" | cut -f 2 -d ' '`
SETTING=`grep CAPTURE_USER_AGENT perma_web/perma/settings/deployments/settings_common.py | sed 's/.*Chrome\/\([^ ]*\)\(.*\)/\1/'`
if [ "$LATEST" != "$SETTING" ] ; then
    perl -pi -e "s/$SETTING/$LATEST/" perma_web/perma/settings/deployments/settings_common.py
    COUNTER=`grep perma3 docker-compose.yml | cut -f 2 -d '.'`
    let NEWCOUNTER=$COUNTER+1
    perl -pi -e "s/perma3:0.$COUNTER/perma3:0.$NEWCOUNTER/" docker-compose.yml
fi
docker-compose down
