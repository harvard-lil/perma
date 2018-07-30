#!/usr/bin/env bash

docker-compose exec web npm shrinkwrap --dev
docker-compose exec web pipenv lock --keep-outdated --pre
docker-compose up -d --build
printf "\n\nYour image has been updated. \n\nIMPORTANT: Please increment the image version for 'web' in docker-compose.yml\n\n"
