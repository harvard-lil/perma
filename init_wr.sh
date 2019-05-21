#!/usr/bin/env bash

docker-compose exec app  python -m webrecorder.admin \
    -c info@perma.cc public Test123Test123 archivist 'Info at Perma.cc'
