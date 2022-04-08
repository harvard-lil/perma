#!/usr/bin/env bash

# Perma database
docker-compose exec web fab dev.init_db

# Perma SSL cert
bash make_cert.sh

# Webrecorder database
docker-compose exec app python -m webrecorder.admin \
    -c info@perma.cc public Test123Test123 archivist 'Info at Perma.cc'
