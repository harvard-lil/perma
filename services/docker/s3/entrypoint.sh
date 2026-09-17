#!/bin/sh
# Create the development and test buckets, then start the gateway.
# With the posix backend, a bucket is a top-level directory under
# $VGW_BACKEND_ARG, so creating the directory creates the bucket.
set -e

mkdir -p "$VGW_BACKEND_ARG/$BUCKET"
mkdir -p "$VGW_BACKEND_ARG/$BUCKET-test"
mkdir -p "$VGW_BACKEND_ARG/$SECONDARY_BUCKET"
mkdir -p "$VGW_BACKEND_ARG/$SECONDARY_BUCKET-test"

# The image's own entrypoint builds the versitygw command line from VGW_* variables.
exec /usr/local/bin/docker-entrypoint.sh "$@"
