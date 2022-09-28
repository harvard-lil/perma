#!/usr/bin/env bash

# Perma database
docker-compose exec web fab dev.init_db

# Perma SSL cert
bash make_cert.sh
