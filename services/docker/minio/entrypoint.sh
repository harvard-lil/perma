#!/bin/bash
# see https://docs.docker.com/engine/reference/builder/#entrypoint
set -e

# Initialize default buckets
mkdir -p "$DATA_DIR/$BUCKET"
mkdir -p "$DATA_DIR/$BUCKET-test"
mkdir -p "$DATA_DIR/$SECONDARY_BUCKET"
mkdir -p "$DATA_DIR/$SECONDARY_BUCKET-test"

# Pass the Docker CMD to the image's original entrypoint script.
exec su -c "/usr/bin/docker-entrypoint.sh $*"
