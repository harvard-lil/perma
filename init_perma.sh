#!/usr/bin/env bash

docker-compose exec web pipenv run fab dev.init_db
