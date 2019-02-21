#!/bin/bash
# see https://docs.docker.com/engine/reference/builder/#entrypoint
# and https://success.docker.com/article/use-a-script-to-initialize-stateful-container-data
set -e

# Make sure these directories exist and are owned by "archivist".
# Must be run as root; configure Docker or Docker-Compose accordingly.
if [ "$1" = 'uwsgi' ]; then
    mkdir -p "$RECORD_ROOT"
    mkdir -p "$STORAGE_ROOT"
    chown -R archivist:archivist "$RECORD_ROOT"
    chown -R archivist:archivist "$STORAGE_ROOT"
fi

# Run the original command, as "archivist".
exec su -m archivist -c "$*"
