#!/usr/bin/env bash

export RUN_ENV=development
python3 manage.py migrate
python3 manage.py runserver 0.0.0.0:8080 --noreload
