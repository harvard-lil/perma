#!/usr/bin/env bash

# This script rebuilds the Docker containers, installing a new version of
# Chrome if available, and updates our user agent and image version number if
# necessary. Rebuilding is somewhat time-consuming, so only run it when you
# have reason to think there's a new Chrome version.

ORIG_CACHE_BUSTER=`grep chrome-layer-cache-buster docker-compose.yml | awk  '{print $2}'`
perl -pi -e "s/chrome-layer-cache-buster: .*/chrome-layer-cache-buster: $(uuidgen)/" docker-compose.yml
docker-compose up -d --build
LATEST=`docker-compose exec -T web bash -c "chromium --version" | cut -f 2 -d ' '`
SETTING=`grep CAPTURE_USER_AGENT perma_web/perma/settings/deployments/settings_common.py | sed 's/.*Chrome\/\([^ ]*\)\(.*\)/\1/'`
if [ "$LATEST" != "$SETTING" ] ; then
    perl -pi -e "s/$SETTING/$LATEST/" perma_web/perma/settings/deployments/settings_common.py
    COUNTER=`grep perma3 docker-compose.yml | cut -f 2 -d '.'`
    let NEWCOUNTER=$COUNTER+1
    perl -pi -e "s/perma3:0.$COUNTER/perma3:0.$NEWCOUNTER/" docker-compose.yml
else
    perl -pi -e "s/chrome-layer-cache-buster: .*/chrome-layer-cache-buster: $ORIG_CACHE_BUSTER/" docker-compose.yml
fi
docker-compose down
