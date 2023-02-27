#!/usr/bin/env bash

docker-compose exec web npm shrinkwrap --dev
docker-compose exec web invoke pip-compile
docker-compose up -d --build
printf "\n\nYour image has been updated."
