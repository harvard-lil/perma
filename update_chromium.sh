#!/usr/bin/env bash

# This script rebuilds the Docker containers, installing a new version of
# Chromium if specified in the Dockerfile, and updates our user agent if necessary.

# first, make sure the intended packages are available
VERSION=`grep CHROMIUM_VERSION= perma_web/Dockerfile | awk -F "=" '{print $2}'`

for ARCH in amd64 arm64 ; do
    curl -s -I "http://security.debian.org/debian-security/pool/main/c/chromium/chromium_${VERSION}_${ARCH}.deb" | grep -q "200 OK" || { echo "$ARCH package for chromium $VERSION is not present, try again later" ; exit 1 ; }
done


docker-compose up -d --build
INSTALLED=`docker-compose exec -T web bash -c "chromium --version" | cut -f 2 -d ' '`
SETTING=`grep CAPTURE_USER_AGENT perma_web/perma/settings/deployments/settings_common.py | sed 's/.*Chrome\/\([^ ]*\)\(.*\)/\1/'`
if [ "$INSTALLED" != "$SETTING" ] && [ "$INSTALLED" != "" ]; then
    perl -pi -e "s/$SETTING/$INSTALLED/" perma_web/perma/settings/deployments/settings_common.py
fi
docker-compose down
